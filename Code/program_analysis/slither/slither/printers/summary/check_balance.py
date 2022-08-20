"""
Module printing summary of the contract
"""
from functools import partial
import logging
from pathlib import Path
import re
from slither.core.variables.local_variable import LocalVariable
from slither.core.expressions.expression import Expression

from slither.slithir.operations.phi import Phi

from slither.slithir.variables.constant import Constant
from slither.slithir.operations.assignment import Assignment
from slither.core.variables.variable import Variable
from slither.printers.summary import slithir
from slither.detectors.reentrancy.reentrancy import AbstractState
from slither.core.expressions import UnaryOperation, UnaryOperationType, literal


from z3 import *
from slither.visitors.expression import left_value
from typing import Mapping, Tuple, List, Dict

from slither.core.declarations import SolidityFunction, Function
from slither.core.variables.state_variable import StateVariable
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.operations import (
    LowLevelCall,
    HighLevelCall,
    Transfer,
    Send,
    SolidityCall,
    condition,
    index,
    transfer,
)
from slither.utils import output
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.colors import green, red, yellow
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.standard_libraries import is_standard_library
from slither.core.cfg.node import Node, NodeType
from slither.utils.tests_pattern import is_test_file
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies, is_dependent_ssa, is_dependent, get_all_dependencies, get_all_dependencies_ssa
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, EventCall, SolidityCall, Binary, Condition
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables import TemporaryVariable, ReferenceVariable
from slither.core.declarations.solidity_variables import *
from slither.utils.myprettytable import MyPrettyTable
from slither.slithir.operations.binary import BinaryType
from slither.slithir.operations import Operation
from slither.core.declarations.function import Function
from slither.slithir.operations.library_call import LibraryCall
from slither.printers.summary.csv_util import CSVUtil
import os

TRANS = 'transfer'
COND = 'CONDITION'
UINT = 'uint256'
EXTRA_EXPR = 'msg.value>=this.balance'
REQUIRE = 'require(bool)'
THIS_BALANCE = 'this.balance'
MAPPING_SEPC = 'mapping(address => uint256)'
ADDRESS = 'address'
OP_AND = '&&'
MSG_VAL = 'msg.value'

SYMBOL_LIST = [
    '>=', '<=', '==', '>', '<', '='
]

class CheckBalance(AbstractPrinter):
    ARGUMENT = 'cb'

    HELP = "Print a human-readable summary of the contracts"
    fname = ''

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#human-summary"

    def output(self, _filename):  # pylint: disable=too-many-locals,too-many-statements
    #     """
    #     _filename is not used
    #         Args:
    #             _filename(string)
    #     """
        self.fname = _filename
        for c in self.contracts:
            if c.is_top_level:
                continue
            f = c.constructor
        self.backward_analysis()           
    
        txt = ''           

        results = {
            "contracts": {"elements": []},
            "number_lines": 0,
            "number_lines_in_dependencies": 0,
            "number_lines_assembly": 0,
            "standard_libraries": [],
            "ercs": [],
            "number_findings": dict(),
            "detectors": [],
        }
 
        json = self.generate_output(txt)
        self.visited_all_paths = {}  # pylint: disable=attribute-defined-outside-init
        return json

    def backward_analysis(self):
        for c in self.contracts:
            for f in c.functions_and_modifiers:
                transfer_node_list = self.find_transfer(f)
                if len(transfer_node_list) == 0:   
                    continue

                for node in transfer_node_list:
                    print('track node ', node)
                    self.track_control_condition(f, node)            

    # explore pre node
    def _explore(self, node: Node, visited, path_list):
        if node in visited:
            return
        visited.append(node)
        # copy && save node 
        tmp_node = [node]
        path_list += tmp_node

        for father in node.fathers:
            self._explore(father, visited, path_list)

    def explore_son(self, node: Node, visited, path_list):
        if node in visited:
            return

        visited.append(node)
        # copy && save node 
        tmp_node = [node]
        path_list += tmp_node

        for son in node.sons:
            self._explore(son, visited, path_list)


    def print_cfg(self, node, path_list: list):
        print('node: ', node)
        for path in path_list:
            print(path)   
        print()     

    def extract_if_loop(self, path_list):
        if_loop_list = []
        for path in path_list:
            if str(path.type) == 'BEGIN_LOOP':
                print('if loop node ', path)
                son_list = []
                self.explore_son(path, [], son_list)
                for son in son_list:
                 #   print('son: ', son)
                    if_loop_list.append(son)

        return if_loop_list

    # unroll loop in a function
    def unroll_loop(self, if_loop_list, f: Function):
        loop_formula_list = []
        symbol_list = ['==', '>=', '<=', '>', '<']

        # find loop count
        pivot_v = None
        pivot_v_init_val = 0
        loop_v = None
        loop_cnt = 0

        parsed_tuple_list = self.condition_to_z3(if_loop_list, f)
        
        for node in if_loop_list:
            rvlist = node.variables_read

            if node.type == NodeType.IFLOOP:
                pivot_v = rvlist[0]

                # loop cnt is value_of(variable_read[1])
                if len(rvlist) > 1:
                    loop_v = rvlist[1]

                    for pt in parsed_tuple_list:
                        if str(pt[0]) == loop_v.name and pt[1] == '=':
                            if isinstance(pt[2], int):
                                loop_cnt = pt[2]    
                # loop cnt is digit; else sth unexpected happened!
                else:
                    node_str = str(node.expression)
                    for symbol in symbol_list:
                        if symbol in node_str:
                            tmp_val = node_str.split(symbol)[1].strip()
                          
                            if tmp_val.isdigit():
                                loop_cnt = int(tmp_val)
                            else:
                                print('pivot value parsed error! ', loop_v)
                                    
                    
        print('loop cnt', loop_cnt)
        
        if loop_cnt == 0:
            return
        print('pivo v ', pivot_v)

        # find initial val of pivot_v
        cnt = 0
        filter_condition_list = []
        pivot_v_init_formula = None

        pivo_condition = None
        for pt in parsed_tuple_list:
            if len(pt) > 1 and pt[1] == '=' and str(pt[0]) == pivot_v.name and cnt == 0:
                pivot_v_init_formula = pt
                cnt += 1
            elif len(pt) > 1 and pt[1] == '=' and str(pt[0]) == pivot_v.name and cnt != 0:
                pt_cnt = 0
                for pt_each in pt:
                    if str(pt_each) == pivot_v.name:
                        pt_cnt += 1 
                    if pt_cnt == 2:
                        pivo_condition = pt
            else:
                filter_condition_list.append(pt)            

        
        # print('pivo cond ', pivo_condition)
        base = pivo_condition[-1]
        print('pvfo: ', pivot_v_init_formula)
        # for fc in filter_condition_list:
        #     print('fc ', fc)

        pivo_loop_condition = pivo_condition
        # try to use a loop to dol

        for i in range(loop_cnt):
            pivot_v_tmp = pivot_v_init_formula.copy()

            filter_loop_condition_list = filter_condition_list.copy()
            print(pivo_condition[-2], ' ', pivo_condition[-1])
            pivot_v_tmp.append(pivo_condition[-2])
            pivot_v_tmp.append(base * i)
            print(pivot_v_tmp)
            filter_loop_condition_list.append(pivot_v_tmp)
            
            self.solve(filter_loop_condition_list)
                
        return loop_formula_list


    def track_control_condition(self, f: Function, node: Node):
        path_list = []                
        self.visited = []

        print('fname ', f.name)
        
        # explore all pre node
        self._explore(node, [], path_list)
        path_list.sort(key=lambda n: n.node_id)
        self.print_cfg(node, path_list)

        # extract loop and unroll to formula
        if_loop_list = self.extract_if_loop(path_list)
        self.unroll_loop(if_loop_list, f)

        seq_path_list = list(set(path_list).difference(set(if_loop_list)))
        self.solve_condition_list(seq_path_list, f)

    def condition_to_z3(self, path_list, f: Function):
        condition_list = []
        condition_var_list = []

        for path in path_list:
            if path == None or str(path) == None:
                continue
            if path.is_conditional():
                condition_list.append(path)
                print('is cond ', path)
                for r in path.variables_read:
                    condition_var_list.append(r)
            elif not path.is_conditional() and '=' in str(path):
                condition_list.append(path) 
                print('is not cond ', path)

        # find all conditions
        condition_list = list(set(condition_list))

        condition_var_list = list(set(condition_var_list))

        # track dataflow of condition variable
        for cv in condition_var_list:
            dataflow = self.track_dataflow_of_condition(cv, f, condition_var_list)
            if len(dataflow) != 0:
                condition_list += dataflow

        condition_list = list(set(condition_list))
        condition_list.sort(key=lambda n: n.node_id)

        z3_var_dict = {}
        state_init_dict = {}
        
        for condition in condition_list:
            read_var_list = condition.variables_read

            for v in read_var_list:
                # get init val of state
                state_val = self.get_state_val(v)
                
                if isinstance(v, StateVariable) and state_val != None:
                    if state_val.isdigit():
                        state_init_dict[str(v)] = int(self.get_state_val(v))

                elif isinstance(v, LocalVariable):
                    bitvec = self.parse_v_to_z3(v)
                    z3_var_dict[v.name] = bitvec
                  
                # find variable that array points to and index
                elif not isinstance(v, SolidityVariableComposed) and not isinstance(v, SolidityVariable):
                    condition_expr = str(condition.expression)
                    if not condition.is_conditional() and ('[' and ']' in  condition_expr):
                        print('cepr ', condition_expr)
                        array_po = condition_expr.split('[')[0]
                        array_full_name = condition_expr.split(']')[0].strip() + ']'
                     
                        array_po_v = [r for r in read_var_list if str(r) == array_po][0]
                       
                        def_v = self.find_defintion_of_v(array_po_v)
                        bitvec = self.parse_v_to_z3(def_v)
                        z3_var_dict[array_full_name] = bitvec

                elif isinstance(v, SolidityVariableComposed):
                    bitvec = self.parse_v_to_z3(v)
                    z3_var_dict[v.name] = bitvec

                elif isinstance(v, SolidityVariable):
                    if v.name == 'this':
                        # print('undefined v ', v, ' type ', type(v))
                        print(condition.expression)
                        this_fullname = 'this.' + str(condition.expression).split('this.')[1].split(' ')[0]
                        # print('full name ', this_fullname)
                        z3_var_dict[this_fullname] = BitVec(this_fullname, 256)

       
        parsed_condition_list = self.parse_condition_list(condition_list)
        # for pc in parsed_condition_list:
        #     print('pc ', pc)

        # for k in state_init_dict.keys():
        #     print(k, ' -> ', state_init_dict[k])   
        parsed_tuple_list = []

        for pc_set in parsed_condition_list:
           # print('pcs ', pc_set)
            for pc_tuple in pc_set:
                each_condition = []
                for pc in pc_tuple:
                    pc_real_val = None
                  
                    if pc in state_init_dict.keys():
                        # print('pc in sid ', pc)
                        pc_real_val = state_init_dict[pc]

                    elif pc in z3_var_dict:
                        pc_real_val = z3_var_dict[pc]

                    elif pc in SYMBOL_LIST:
                        pc_real_val = pc

                    else:
                        if str(pc).isdigit():
                            pc_real_val = int(str(pc))
                        else:
                            pc_real_val = pc      
                        
                    each_condition.append(pc_real_val)
                parsed_tuple_list.append(each_condition)
        
        return parsed_tuple_list 


    def solve_condition_list(self, path_list, f: Function):
        parsed_tuple_list = self.condition_to_z3(path_list, f)
        self.solve(parsed_tuple_list, f.name)

    def solve(self, parsed_tuple_list, fucname):
        solver = Solver()

        print('solving ')

        # for pt in parsed_tuple_list:
        #     for pt_op in pt:
        #         print('op: ', pt_op, type(pt_op))
        
        for pt in parsed_tuple_list:
            is_bal = is_mv = False
            bal_bv = mv_bv = None
            # print('pt ', pt)
            for pt_op in pt:  
                if isinstance(pt_op, BitVecRef):
                    if str(pt_op) == THIS_BALANCE:
                        is_bal = True
                        bal_bv = pt_op
                    if str(pt_op) == MSG_VAL:
                        is_mv = True
                        mv_bv = pt_op

            if is_bal and is_mv:
               # print('bal ', bal_bv, ' mv ', mv_bv)
                parsed_tuple_list.append([bal_bv, '=', bal_bv, '+', mv_bv])
                break   

        print(parsed_tuple_list)
        for pt in parsed_tuple_list:
            for i in range(len(pt)):
                if isinstance(pt[i], str):
                    if pt[i] == '==':
                        # print(' is condition ')
                        continue
                    
                    if pt[i] == '=':
                        lft_op, rht_op = self.parse_single_formula(pt, i)
                        # print(lft_op == rht_op)
                        solver.add(lft_op == rht_op)

                    if pt[i] == '>=':
                        # print('pt 0 ', pt[0], type(pt[0]), '   i + 1 ', pt[i + 1], ' ', type(pt[i + 1]))
                        solver.add(pt[0] >= pt[1 + i], pt[0] > 0, pt[i + 1] > 0)

        print('check ')
        check_list = []
        if solver.check() == unsat:
            print('fname')
            CSVUtil.write_csv('csv/unstat_pro.csv', [], [self.fname, fucname, parsed_tuple_list])
            print(self.fname)
            cmd = 'mv ' + self.fname + ' ' + 'unstat3/'
           # os.system(cmd)

    def parse_single_formula(self, pt, i):
        ar_symbol_list = ['+', '-', '*', '/']
        lft_op = pt[0]
        rht_op = pt[i + 1]
        
        for j in range(0, i):
            if str(pt[j]) in ar_symbol_list:
                print('need parse arith lft....')
                lft_symbol = pt[j]
                                    
                if lft_symbol == '+':
                    lft_op = pt[0] + pt[j + 1]
                
                if lft_symbol == '-':
                    lft_op = pt[0] - pt[j + 1]

                if lft_symbol == '*':
                    lft_op = pt[0] * pt[j + 1]

                if lft_symbol == '/':
                    lft_op = pt[0] / pt[j + 1]    
                            
        for j in range(i + 1, len(pt) - 1):
            if str(pt[j]) in ar_symbol_list:
                print('need parse arith lft....')
                rht_symbol = pt[j]
                                    
                if rht_symbol == '+':
                    rht_op = pt[i + 1] + pt[j + 1]
                            
                if rht_symbol == '-':
                    rht_op = pt[i + 1] - pt[j + 1]

                if rht_symbol == '*':
                    rht_op = pt[i + 1] * pt[j + 1]

                if rht_symbol == '/':
                    rht_op = pt[i + 1] / pt[j + 1]

        return lft_op, rht_op

    def parse_condition_list(self, conidtion_list):
        parsed_condition_list = []

        for condition in conidtion_list:
            parsed_condition = self.parse_single_condition(condition)
            parsed_condition_list.append(parsed_condition)

        return parsed_condition_list    

    def parse_single_condition(self, condition: Node):
        parsed_condition_list = []        

        arithmetic_symbol_list = ['+', '-', '*', '/']
        eq_symbol_list = [ '+=', '<=', '=']

        condition_str = str(condition.expression)

        if REQUIRE in condition_str:
            condition_str = condition_str.split(REQUIRE)[1].split('(')[1].split(')')[0]

        read_var_list = condition.variables_read
        write_var_list = condition.variables_written

        if condition.is_conditional():

            if '&&' in condition_str:
                t0 = condition_str.split('&&')[0].strip()
                t1 = condition_str.split('&&')[1].strip()

                parsed_condition_list.append(self.extract_condition_str(t0, read_var_list, write_var_list))
                parsed_condition_list.append(self.extract_condition_str(t1, read_var_list, write_var_list))
            
            else:
                parsed_condition_list.append(self.extract_condition_str(condition_str, read_var_list, write_var_list))
            return parsed_condition_list    
        else:
            for eqsymbol in eq_symbol_list:      
                if '+=' in condition_str or '-=' in condition_str:
                    op = condition_str.split('=')[0][-1] + '='
                    op_lft = condition_str.split(op)[0].strip()
                    op_rht = condition_str.split(op)[1].strip()
                
                    parsed_condition_list.append((op_lft, '=', op_lft, op[0], op_rht))
                    return parsed_condition_list
                    
                if eqsymbol in condition_str:
                    lft_var = condition_str.split(eqsymbol)[0].strip()
                    rht_var = condition_str.split(eqsymbol)[1].strip()

                    if '(' in lft_var:
                        lft_var = lft_var.split('(')[1]

                    if ')' in lft_var:
                        lft_var = lft_var.split(')')[0]    
                        
                    if '(' in rht_var:
                        rht_var = rht_var.split('(')[1]

                    if ')' in rht_var:
                        rht_var = rht_var.split(')')[0]    
                    
                    for asymbol in arithmetic_symbol_list:
                        if asymbol in rht_var:
                            op_lft = rht_var.split(asymbol)[0].strip()
                            op_rht = rht_var.split(asymbol)[1].strip()

                            parsed_condition_list.append((lft_var, eqsymbol, op_lft, asymbol, op_rht))
                            
                            return parsed_condition_list

                    parsed_condition_list.append((lft_var, eqsymbol, rht_var))
                    return parsed_condition_list

    def extract_condition_str(self, condition_str: str, read_var_list, write_var_list):
        lft_op = rht_op = sym = None
        symbol_list = ['>', '<', '>=', '<=', '==']
        for symbol in symbol_list:
            if symbol in condition_str:
                lft_op = condition_str.split(symbol)[0].strip()
                rht_op = condition_str.split(symbol)[1].strip()
                sym = symbol

        return (lft_op, sym, rht_op)

    def track_dataflow_of_condition(self, v: Variable, f: Function, condition_var_list: list):
        dataflow = []

        for node in f.nodes: 
            if v in node.variables_written:
                dataflow.append(node)
        return dataflow

    def get_state_val(self, v: Variable):
        if not isinstance(v, StateVariable):
            return None

        for c in self.contracts:
            ini_val = v._initial_expression
            if ini_val != None:
                
                return str(ini_val)

    def parse_v_to_z3(self, v: Variable):
        if str(v) == THIS_BALANCE:
            return BitVec(v.name, 256)
        v_type = self.parse_v_type(str(v.type))
        return {
            UINT: BitVec(v.name, 256),
            ADDRESS: BitVec(v.name, 20),

        }[v_type]

    def find_defintion_of_v(self, v: Variable):
        if isinstance(v, StateVariable):
            return v
      
    # convert to solidity data type
    def parse_v_type(self, type_str):
        type_dict = SOLIDITY_VARIABLES_COMPOSED.copy()
        type_dict[MAPPING_SEPC] = UINT
        type_dict[UINT] = UINT
        type_dict[ADDRESS] = ADDRESS
        # print('type str ', type_str)
        type_dict[THIS_BALANCE] = UINT

        return type_dict[type_str]

    def find_transfer(self, f: Function):
        transfer_node_list = []

        for node in f.nodes:
            if node.can_send_eth and node.type != NodeType.ENTRYPOINT:
                if 'transfer' in str(node.expression):
                    transfer_node_list.append(node)
            
        return transfer_node_list