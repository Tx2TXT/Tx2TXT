"""
    Module printing summary of the contract
"""

from ast import Load
from re import A
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies, is_dependent_ssa, is_dependent, get_all_dependencies, get_all_dependencies_ssa
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, EventCall, SolidityCall, Binary
from slither.slithir.variables.temporary import TemporaryVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.variables import TemporaryVariable, ReferenceVariable
from slither.utils.myprettytable import MyPrettyTable
from slither.slithir.operations.binary import BinaryType
from slither.slithir.operations import Operation
from slither.core.declarations.function import Function
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.utils.tranfer_var_dict import TransferVarDict
import time

from slither.slithir.operations.high_level_call import HighLevelCall

from slither.slithir.operations.library_call import LibraryCall
from slither.printers.summary.csv_util import CSVUtil
import os
import csv

PLUS = '+'
MINUS = '-'
WITHDRAW = 'withdraw'
TRANSFER = 'transfer'
MATH_LIB = 'SafeMath'
ADD = 'add'
SUB = 'sub'

TRANSFERFROM = 'transferFrom'

OUT_DIR = '/Users/py/github/slither/out'
SP = ' '

def _get(v, c):
    return list(
        {
            d.name

            for d in get_dependencies(v, c)
            if not isinstance(d, (TemporaryVariable, ReferenceVariable))
        }
    )

def _get_all(v, c):
    return list(
        {
            d.name
            for d in get_dependencies(v, c)
        }
    )

def get_dependency(v, c):
    return list(
        {
            d
            for d in get_dependencies(v, c)
            if not isinstance(d, (TemporaryVariable, ReferenceVariable))
        }
    )


class Graph(AbstractPrinter):

    ARGUMENT = "graph"
    HELP = "Print the data dependencies of the variables"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#data-dependencies"


    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """
        start = time.time()
        self.fname = _filename
        all_tables = []
        all_txt = ""

        txt = ""

        for c in self.contracts:
            if c.is_top_level:
                continue

            table = MyPrettyTable(["", ""])

            self.info(txt)

            all_txt += txt
            all_tables.append((c.name, table))

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        for c in self.contracts:
            for f in c.functions_and_modifiers:
                
                self.find_moneyflow(f, c)
        end = time.time()
        with open('time.csv', 'a+') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow([end-start])

       
        return res

    def find_moneyflow(self, f: Function, c):
        node_list = f.nodes
        transfer_id = 0

        for node in node_list:
            
            if TRANSFERFROM in str(node):
                print('find transferFrom.... ', str(node))
                # with open('transferFrom_sol.txt', 'a+') as f:
                #     f.write(self.fname + '_' + f.name + '\n')
                condition_list = self.find_condition_list(node.node_id, f)

                transfer_node = node

                

                for ir in node.irs:
                    if isinstance(ir, HighLevelCall):
                        # transfer from function
                        if ir.function_name == TRANSFERFROM:
                            print('find var ir ....')
                            print(ir)

                            to_addr_org = ir.arguments[1]

                            if isinstance(to_addr_org, TemporaryVariable):
                                nid = str(to_addr_org.index)
                               
                                expr = 'TMP_' + nid + ' ='
                             
                                cfg_str_list = self.slithir_cfg_to_dot_str(f).split('\n')
                                for node in cfg_str_list:
                                    # print(node)
                                    if expr in node:
                                        # print('find nid ', str(node))
                                        if 'CONVERT' and 'to' in str(node):
                                            ir.arguments[1] = str(node).split('=')[1].replace('CONVERT', '').replace('to', 
                                            '').strip()


                                
                            arg_list = [str(x) for x in ir.arguments]      
                            from_addr, to_addr, amount = arg_list[0], arg_list[1], arg_list[2]
                            data_node_id_list = self.find_data_dependency_flow(ir.arguments[-1], c, f)
                            

                            print('amount ---- ', amount)
                            for dnid in data_node_id_list:
                                print('dnid ', dnid)

                            amount_var = ir.arguments[2]
                            print('amount var ', amount_var)

                            # get data dependency var of `money amount`
                            dep_list = _get(amount_var, c)   

                            another_dep_list, def_list = self.find_data_dependency_flow(amount_var, c, f)
                            print('ADL ')
                            for ad in another_dep_list:
                                print(ad)

                            data_node_list = []

                            for data_def in def_list:
                                for n in node_list:
                                    if str(n.expression) == data_def:
                                        data_node_list.append(n)
                                        print('data node ', str(n.expression))

                            
                            domain_sen = ''


                            if isinstance(amount_var, LocalVariable):
                                amt_var_str = str(amount_var.expression)
                                if 'balanceOf' in amt_var_str:
                                    balance_domain = amt_var_str.split('.balanceOf')[0]
                                    if '_' in  amt_var_str:
                                        balance_domain = amt_var_str.split('_')[0]

                                    domain_sen = amount_var.name + ' is the balance of ' + balance_domain
                                    dep_list = []

                            print('domain sen ', domain_sen)

                            description_list = []
                            # write descriptions to file
                            res_name = 'res/' + str(self.fname).split('/')[-1] + '_' + f.name + '.txt'
                          

                            transfer_sentence = 'in function %s, transfer (%s) from (%s) to (%s)' %(f.name, amount,
                                from_addr, to_addr)
                            for condition_sentence in condition_list:
                                description = transfer_sentence + ' under the condition that ' + str(condition_sentence)
                                print(description)
                                description_list.append(description) 
                            
                            
                            if len(dep_list) != 0:
                                for dep in dep_list:
                                    data_node_id_list = self.find_dataflow(dep, f)
                                    print('dep name ', dep)
                                    for dnid in data_node_id_list:
                                        print('dnid ', dnid)
                                    for dn in data_node_id_list:
                                        dn_sentence = str(dn).replace('EXPRESSION', '').replace('IF', 'if').replace('NEW VARIABLE', '')
                                        condition_list = self.find_condition_list(dn.node_id, f)
                                        # print('sc ', condition_list)
                                        for condition_sentence in condition_list:
                                       
                                            description = dn_sentence + ' under the condition that ' + str(condition_sentence) + '\n'
                                            
                                            description_list.append(description)
                            else:
                               
                                description_list.append(domain_sen)
                                print(len(description_list))

                            if len(description_list) != 0:
                                with open(res_name, 'w') as res_f:
                                    
                                    res_f.write("\n".join(description_list))

                            analysis_node_cnt = len(set(description_list))
                            total_node_cnt = len(f.nodes) 
                            rs = [c.name, f.name, str(total_node_cnt), str(analysis_node_cnt)]
                            with open('res/node.csv', 'a+') as csvfile: 
                                csvwriter = csv.writer(csvfile) 
                                csvwriter.writerow(rs) 

                            cond_node_list = []
                            cond_node_list.append(transfer_node)
                            
                            for sig_cond in condition_list:
                                for cond in sig_cond:
                                    if 'IF_LOOP' in cond:
                                        cond = cond.split('IF_LOOP')[1].strip()
                                    for node in f.nodes:
                                        if str(node.expression) == cond:
                                            cond_node_list.append(node)
                                        if str(node) == cond:
                                            cond_node_list.append(node)
                                        for ir in node.irs:
                                            if cond == ir:
                                                cond_node_list.append(node)
                                            
                            
                            cond_node_list = list(set(cond_node_list))

                            cond_node_list += data_node_list

                            graph_ir = self.node_list_to_dot_str(cond_node_list)
                            # print(graph_ir)

                            with open('ic.txt', 'w') as f:
                                f.write(graph_ir)   

    def find_data_dependency_flow(self, var, c, f: Function):
        data_dep_list = get_dependency(var, c)
        data_dep_list.append(var)

        def_list = []
        for dep in data_dep_list:
            for node in f.nodes:
                if '=' in str(node.expression) and '==' not in str(node.expression):
                    lft_val_str = str(node.expression).split('=')[0]
                    dep_name = dep.name
                  
                    if dep_name in lft_val_str.strip():
                        print(dep_name)
                        print(node.expression, ' ', node.type)
                        if str(node.expression) not in def_list:
                            def_list.append(str(node.expression))

        for def_ins in def_list:
            print('def ins ', def_ins)

        return data_dep_list, def_list

        
                                    
    def find_dataflow(self, var: LocalVariable, f: Function):
        node_list = []
        for node in f.nodes:
            if str(var) in str(node):
                if 'setBalance' in str(node) or TRANSFERFROM in str(node) or \
                'IF' in str(node) or 'require' in str(node):
                    continue
                node_list.append(node)

        return node_list       

    def is_condition_node(self, node: Node):
        if node.type == NodeType.IF or node.type == NodeType.IFLOOP or \
        (node.type == NodeType.EXPRESSION and 'require' in str(node)):
            return True        

    def find_condition_list(self, node_id: int, f: Function):
        xor_node_list = []
        pre_node_list = []
        condition_list = []


        pre_node_list, xor_node_list = self.find_control_flow(node_id, f)
        
        # rm xor node
        for xor_node in xor_node_list:
            if xor_node in pre_node_list:
                pre_node_list.remove(xor_node)

        for node in pre_node_list:
            if self.is_condition_node(node):
                condition_list.append(str(node))

        # set for all xor conditon list
        xor_node_list_set = []  
        for node in xor_node_list:
            if self.is_condition_node(node):
                true_cond = str(node)
                false_cond = '!(' + str(node) + ')'
                
                # print('true cond ', true_cond)

                if len(xor_node_list_set) == 0:
                    xor_node_list_set.append([true_cond])
                    xor_node_list_set.append([false_cond])
                else:
                    # append true and false branches to xor condition list
                    xor_node_list_set_cp = xor_node_list_set.copy()

                    for former_xor_node_list in xor_node_list_set_cp:
                        former_xor_node_list_cp = former_xor_node_list.copy()

                        former_xor_node_list.append(true_cond)
                        former_xor_node_list_cp.append(false_cond)

                        xor_node_list_set.remove(former_xor_node_list)
                        xor_node_list_set.append(former_xor_node_list)
                        xor_node_list_set.append(former_xor_node_list_cp) 

        # print('xor set ', xor_node_list_set)
        if len(xor_node_list_set) == 0:
            xor_node_list_set = [condition_list]
        else:
            # print(xor_node_list_set)
            for xor_node_list in xor_node_list_set:
                # print('xor node list')
                xor_node_list += condition_list

        condition_sentence_set = []
        # condition_list_set = []
        for xor_node_list in xor_node_list_set:
            # for condition_list in xor_node_list:
                        # print('cond list: ', condition_list)
                        condition_sentence = ', '.join(condition_list)
                        condition_sentence = condition_sentence.replace('EXPRESSION', '')
                        condition_sentence = condition_sentence.replace('IF', 'if')
                        condition_sentence_set.append(condition_sentence)
        return xor_node_list_set      
  
    def find_control_flow(self, node_id: int, f: Function):
        cfg_str_list = self.slithir_cfg_to_dot_str(f).split('\n')
        link_node_list = []

        br_link_node_list = []
        xor_link_node_list = []
        if_link_node_id_list = []

        for cfg_str in cfg_str_list:
            if '[label="Node Type: IF' in  cfg_str:
                    if_link_node_id_list.append(cfg_str.split('[la')[0])   
            if '->' in cfg_str:
                if '[label="False"]' in cfg_str:
                    br_link_node_list.append(cfg_str)
                    
                if '[' in cfg_str:
                    format_cfg_str = cfg_str.split('[')[0] + ';'
                    link_node_list.append(format_cfg_str)
                link_node_list.append(cfg_str)    
        i = 0
        pre_node_id_list = []
   
        format_link_node_list = []
        for link_node in link_node_list:
            if '[label' in link_node:
                link_node = link_node.split('[')[0] + ';'
            format_link_node_list.append(link_node)

      
        while i < len(format_link_node_list):
            i = 0
            for link_node in format_link_node_list:
                cur_node_id = link_node.split('->')[1].split(';')[0]
               
                if cur_node_id == str(node_id):
                    pre_node_id = link_node.split('->')[0]
                    # print('find pre node ', pre_node_id)
                    pre_node_id_list.append(pre_node_id)
                    node_id = pre_node_id
                    break
                else:
                    i += 1    

        xor_link_node_id_list = []

        endif_node_id_list = []

        for if_node_id in if_link_node_id_list:
            for cfg_str in cfg_str_list:
                if '->' in cfg_str:
                    if cfg_str.split('->')[0] == if_node_id and '[label="False"]' in cfg_str:
                        rht_node_id = cfg_str.split('->')[1].split('[')[0]

                        if rht_node_id in pre_node_id_list:
                            # end if 
                            for link_node in cfg_str_list:
                                # print('ln ', link_node)
                                if '[label' in link_node:
                                    if link_node.split('[label')[0] == rht_node_id:
                                        endif_node_id_list.append(rht_node_id)                                        
                                    else:
                                        xor_link_node_id_list.append(if_node_id)

        xor_link_node_id_list = list(set(xor_link_node_id_list))
        rm_node_id_list = []

        pre_node_list = []
        xor_node_list = []
        condition_list = []

        for node in f.nodes:
            if str(node.node_id) in pre_node_id_list:
                pre_node_list.append(node)
            if str(node.node_id) in xor_link_node_id_list:
                xor_node_list.append(node)

        for xor_node in xor_node_list:
            if xor_node in pre_node_list:
                pre_node_list.remove(xor_node)

        return pre_node_list, xor_node_list 

    def node_list_to_dot_str(self, node_list, skip_expressions=False) -> str:
        from slither.core.cfg.node import NodeType

        content = ""
        content += "digraph{\n"
        for node in node_list:
            label = "Node Type: {} {}\n".format(str(node.type), node.node_id)
            if node.expression and not skip_expressions:
                label += "\nEXPRESSION:\n{}\n".format(node.expression)
            if node.irs and not skip_expressions:
                label += "\nIRs:\n" + "\n".join([str(ir) for ir in node.irs])
            content += '{}[label="{}"];\n'.format(node.node_id, label)
            if node.type in [NodeType.IF, NodeType.IFLOOP]:
                true_node = node.son_true
                if true_node:
                    content += '{}->{}[label="True"];\n'.format(node.node_id, true_node.node_id)
                false_node = node.son_false
                if false_node:
                    content += '{}->{}[label="False"];\n'.format(node.node_id, false_node.node_id)
            else:
                for son in node.sons:
                    content += "{}->{};\n".format(node.node_id, son.node_id)

        content += "}\n"
        return content           

    def slithir_cfg_to_dot_str(self, f: Function, skip_expressions=False) -> str:
        from slither.core.cfg.node import NodeType

        content = ""
        content += "digraph{\n"
        for node in f.nodes:
            label = "Node Type: {} {}\n".format(str(node.type), node.node_id)
            if node.expression and not skip_expressions:
                label += "\nEXPRESSION:\n{}\n".format(node.expression)
            if node.irs and not skip_expressions:
                label += "\nIRs:\n" + "\n".join([str(ir) for ir in node.irs])
            content += '{}[label="{}"];\n'.format(node.node_id, label)
            if node.type in [NodeType.IF, NodeType.IFLOOP]:
                true_node = node.son_true
                if true_node:
                    content += '{}->{}[label="True"];\n'.format(node.node_id, true_node.node_id)
                false_node = node.son_false
                if false_node:
                    content += '{}->{}[label="False"];\n'.format(node.node_id, false_node.node_id)
            else:
                for son in node.sons:
                    content += "{}->{};\n".format(node.node_id, son.node_id)

        content += "}\n"
        return content

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
