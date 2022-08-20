"""
    Module printing summary of the contract
"""

from ast import Load
from audioop import reverse
from curses.ascii import isdigit
from dis import code_info
from re import A
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies, is_dependent_ssa, is_dependent, get_all_dependencies, get_all_dependencies_ssa
from slither.slithir.operations import OperationWithLValue, InternalCall, EventCall, SolidityCall, Binary
from slither.slithir.variables.temporary import TemporaryVariable
from  slither.slithir.variables.state_variable import StateVariable
import pydot

from slither.slithir.variables import TemporaryVariable, ReferenceVariable
from slither.utils.myprettytable import MyPrettyTable
from slither.slithir.operations.binary import BinaryType
from slither.slithir.operations import Operation
from slither.core.declarations.function import Function
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.utils.erc20_api import ERC20_API
from slither.core.expressions.binary_operation import BinaryOperation


from slither.slithir.operations.high_level_call import HighLevelCall

import csv

PLUS = '+'
MINUS = '-'
WITHDRAW = 'withdraw'
TRANSFER = 'transfer'
MATH_LIB = 'SafeMath'
ADD = 'add'
SUB = 'sub'
ERC20 = 'ERC20'
SCOPE = '_scope_'

TRANSFERFROM = 'transferFrom'
CONST = 'constant'

OUT_DIR = '/Users/py/github/slither/out'
SP = ' '
STATE_VARIABLE = 'state variable'

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


class TokenGraph(AbstractPrinter):

    ARGUMENT = "graph+"
    HELP = "Print the data dependencies of the variables"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#data-dependencies"


    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """
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
       
        return res

    def value_inter_analysis(self, f: Function, arg):
        node_list = f.nodes
        ir_list = []

        for n in node_list:
            for ir in n.irs:
                ir_list.append(ir)

        for ir in ir_list:
            if isinstance(ir, InternalCall) and ir.lvalue == arg:
                # print('* ir ', ir)
                func_name = ir.function_name
                contract_name = ir.contract_name
                
                for c in self.contracts:
                    if c.name == contract_name:
                        for f in c.functions_and_modifiers:
                            if f.name == func_name:
                                # print('find f %s in contract %s' % (func_name, contract_name))
                                # print('return vals ')
                                for rt in f.returns:
                                    for node in f.nodes:
                                        for ir in node.irs:
                                            if isinstance(ir, Assignment):
                                                if ir.lvalue == rt:
                                                    if type(ir.rvalue) == Constant:
                                                        # constant returns
                                                        return CONST
                                                else:
                                                    return ir.rvalue                       
              

    def find_token_api(self, f: Function, c):
        node_list = f.nodes
        ir_list = []

        for n in node_list:
            for ir in n.irs:
                ir_list.append(ir)

        for node in node_list:
            # if erc20 interface
            if ERC20 in str(node.expression):
                for node_ir in node.irs:
                    if isinstance(node_ir, HighLevelCall):
                        func_name = node_ir.function_name

                        constant_arg_list = []
                        api_arg_list = []
                        for arg in node_ir.arguments:
                            if isinstance(arg, TemporaryVariable):
                                real_val = self.value_inter_analysis(f, arg)
                                # print('real val ', real_val)
                                if real_val == CONST:
                                    constant_arg_list.append(arg)
                                api_arg_list.append(real_val)
                            elif isinstance(arg, LocalVariable):
                                api_arg_list.append(arg)
                            elif isinstance(arg, Constant):
                                constant_arg_list.append(arg)
                            else:
                                print('extra arg ', arg, ' ', type(arg))     

                          
                        erc20_api =  ERC20_API(func_name, api_arg_list) 
                        erc20_description = erc20_api.get_description()
                        print('erc20_description: ', erc20_description)

    def find_moneyflow(self, f: Function, c):
        self.find_token_api(f, c)
        node_list = f.nodes

        for node in node_list:
            if TRANSFERFROM in str(node):
                print('find transferFrom.... ', str(node))
                condition_list = self.find_condition_list(node.node_id, f)

                print('cond list')
                print(condition_list)

                transfer_node = node

                for ir in node.irs:
                    if isinstance(ir, HighLevelCall):
                        # transfer from function
                        if ir.function_name == TRANSFERFROM:
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
                            self.find_dirct_control_node(19, f)     
                            from_addr, to_addr, amount = arg_list[0], arg_list[1], arg_list[2]

                            from_addr_var, to_addr_var, amount_var = ir.arguments[0], ir.arguments[1], ir.arguments[2]

                            # get data dependency var of `money amount`
                            dep_list = get_dependency(amount_var, f)

                            balance_nl = self.track_balance(from_addr_var, to_addr_var, c, f)

                            source_nl_list = self.convert_dataflow_node_to_nl(amount_var, c, f) 
                            
                            another_dep_list, def_list = self.find_data_dependency_flow(amount_var, c, f)
                            data_node_list = []

                            for data_def in def_list:
                                for n in node_list:
                                    if str(n.expression) == data_def:
                                        data_node_list.append(n)
                                        # print('data node ', str(n.expression))
                            domain_sen = ''

                            if isinstance(amount_var, LocalVariable):
                                amt_var_str = str(amount_var.expression)
                                if 'balanceOf' in amt_var_str:
                                    balance_domain = amt_var_str.split('.balanceOf')[0]
                                    if '_' in  amt_var_str:
                                        balance_domain = amt_var_str.split('_')[0]

                                    domain_sen = amount_var.name + ' is the balance of ' + balance_domain
                                    # print('true bof ')
                                    # print('dsn ', domain_sen)
                                    dep_list = []

                            # print('domain sen ', domain_sen)
                            description_list = []
                            # write descriptions to file
                            res_name = 'res/erc20/' + str(self.fname).split('/')[-1] + '_' + f.name + '.txt' 

                            cfg_node_len = len(condition_list)
                            df_node_len = 0                

                            erc20_api =  ERC20_API(TRANSFERFROM, [from_addr, to_addr, amount])
                            cfg_description_list = [] 
                            transfer_sentence = 'The function %s ' %(f.name) + erc20_api.get_description()
                            for condition_sentence in condition_list:
                                if SCOPE in condition_sentence:
                                    pre_part = condition_sentence.split(SCOPE)[0]
                                    digit = condition_sentence.split(SCOPE)[1].split(' ')[0]
                                    post_part = condition_sentence.split(SCOPE + digit)[1]
                                    condition_sentence = pre_part + ' ' + post_part
                                
                                description = transfer_sentence 
                                # description = transfer_sentence + ' It is under the condition that ' + str(condition_sentence)
                                # print(description)
                                cfg_description_list = [transfer_sentence]
                            
                            df_description_list = []
                            final_cond_list = []

                            if len(dep_list) != 0:
                                for dep in dep_list:
                                    # print(
                                    #     'dep in dl: ', dep
                                    # )
                                    data_node_id_list = self.find_dataflow(dep, f, c)
                                    # for dn in data_node_id_list:
                                    #     print('dn ', dn)
                                    for dn in data_node_id_list:
                                        dn_sentence = str(dn).replace('EXPRESSION', '').replace('IF', 'if').replace('NEW VARIABLE', '')
                                        condition_list = self.find_condition_list(dn.node_id, f)
                                        # print('cond of ', dn)
                                        # print(condition_list)
                                        if len(condition_list) > len(final_cond_list):
                                            final_cond_list = condition_list
                                            df_node_len = len(condition_list)

                                        df_description_list.append(dn_sentence)    
                                
                                        # for condition_sentence in condition_list:
                                        #     if SCOPE in condition_sentence:
                                        #         pre_part = condition_sentence.split(SCOPE)[0]
                                        #         digit = condition_sentence.split(SCOPE)[1].split(' ')[0]
                                        #         post_part = condition_sentence.split(SCOPE + digit)[1]
                                        #         condition_sentence = pre_part + ' ' + post_part

                                        #     if len(condition_sentence) == 0:
                                        #         description = dn_sentence
                                        #     else:    
                                        #         description = dn_sentence + ' under the condition that ' + str(condition_sentence)          
                                        #     df_description_list.append(description)

                                            # print('dn sentence ', dn_sentence)
                            else:
                                df_description_list.append(domain_sen)
                            # print(description_list)
                            # print('ndf ** ')
                            # print(df_description_list)

                            com_description_list = []

                            for condition_sentence in final_cond_list:
                                if SCOPE in condition_sentence:
                                    pre_part = condition_sentence.split(SCOPE)[0]
                                    digit = condition_sentence.split(SCOPE)[1].split(' ')[0]
                                    post_part = condition_sentence.split(SCOPE + digit)[1]
                                    condition_sentence = pre_part + ' ' + post_part

                                if len(condition_sentence) == 0:
                                    continue
                                else:    
                                    description = ' under the condition that ' + str(condition_sentence)
                                    df_cp = df_description_list.copy()
                                    df_cp.append(description)         
                                    com_description_list.append(df_cp)

                            
                            # print('desp ')
                            com_str_description_list = []
                            for cd in com_description_list:
                                cd_str = ''
                                for tu in cd:
                                    cd_str += tu + ', '
                                cd_str + '\n'
                                com_str_description_list.append(cd_str)    

                            # print(com_str_description_list)
                            description_str = ','.join(cfg_description_list) + '\n' + balance_nl
                            for snl in source_nl_list:
                                description_list.append(snl + description_str)
                            if len(description_list) != 0:
                                with open(res_name, 'w') as res_f:   
                                    res_f.write("\n".join(description_list))

                            analysis_node_cnt = len(set(description_list))
                            total_node_cnt = len(f.nodes) 
                            rs = [c.name, f.name, str(cfg_node_len), str(df_node_len)]

                            print('cfg node len ', cfg_node_len)
                            print('df node len ', df_node_len)
                            with open('res/erc20/node.csv', 'a+') as csvfile: 
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

                            with open('graph/' + str(self.fname).split('/')[-1] + '_' + f.name + '.dot', 'w') as f:
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
                        if str(node.expression) not in def_list:
                            def_list.append(str(node.expression))

        return data_dep_list, def_list
                                    
    def find_dataflow(self, var: LocalVariable, f: Function, c):
        node_list = []
        # get data dependency node
        data_dep_list = _get(var, f)

        sv_list = get_dependency(var, f)
                
        if len(data_dep_list) == 0:
            data_dep_list = [var]

        for dd in data_dep_list:
            for node in f.nodes:
                if dd in [str(vw) for vw in node.variables_written] and dd not in node_list:
                    node_list.append(node)
        
                            
        return node_list 

    # convert dataflow node expression to natural language
    def convert_dataflow_node_to_nl(self, var: LocalVariable, c, f: Function):
        data_nl_list = []

        if var in f.parameters:
            data_nl_list.append('The variable amount is from user input.')
        
        sv_list = [sv for sv in f.all_state_variables_written() if is_dependent(var, sv, c)]
        sv_str_list = [str(sv) for sv in sv_list]

        var_def_list = self.find_all_defs(var, f)
        var_def_dict = {}

        state_var_list = f.all_state_variables_read() + f.all_state_variables_written()
        for sv in state_var_list:
            var_def_dict[sv] = [STATE_VARIABLE]
        


        for param in f.parameters:
            var_def_dict[param] = ['input ' + str(param.type)]

        dd_var_list = get_dependency(var, c)
        for dd_var in dd_var_list:
            def_list = self.find_all_defs(dd_var, f)
            if type(dd_var) == StateVariable:
                var_def_dict[dd_var] = [STATE_VARIABLE]
            elif len(def_list) == 0:
                continue    
            else:
                var_def_dict[dd_var] = self.find_all_defs(dd_var, f)

        
        var_def_cnt_dict = {}
        for k, v in var_def_dict.items():
                
            var_def_cnt_dict[k] = len(v)

        print(
            
            'vdcd ', var_def_cnt_dict
        )        

        mul_path_sen_list = []
        for k, v in var_def_cnt_dict.items():
            if v > 1:
                
                
                k_def = var_def_dict[k]
                for v0 in k_def:
                    v_sen = ''
                    k_expr = self.convert_single_node_to_nl(v0, f, var_def_dict, var)
                    pre_node_list, xor_node_list = self.find_control_flow(v0.node_id, f)
                    
                    for pn in pre_node_list:
                        if pn.is_conditional():
                            condition_sen = 'If ' + self.convert_single_node_to_nl(pn, f, var_def_dict, var) + ', '
                            v_sen += condition_sen
                    v_sen += k_expr        
                    mul_path_sen_list.append(v_sen)

        print('mul paths ', mul_path_sen_list, len(mul_path_sen_list))

        if len(mul_path_sen_list) >= 6:
            r0 = mul_path_sen_list[0] + ', ' + mul_path_sen_list[2] + ', ' +  mul_path_sen_list[4]
            r1 = mul_path_sen_list[0] + ', ' + mul_path_sen_list[2] + ', ' +  mul_path_sen_list[5]
            r2 = mul_path_sen_list[0] + ', ' +  mul_path_sen_list[3] + ', ' +  mul_path_sen_list[4]
            r3 = mul_path_sen_list[0] + ', ' + mul_path_sen_list[2] + ', ' + mul_path_sen_list[5]
            r4 = mul_path_sen_list[1] + ', ' +  mul_path_sen_list[2] + ', ' +  mul_path_sen_list[4]
            r5 = mul_path_sen_list[1] + ', ' +  mul_path_sen_list[2] + ', ' +  mul_path_sen_list[5]
            r6 = mul_path_sen_list[1] + ', ' +  mul_path_sen_list[3] + ', ' +  mul_path_sen_list[4]
            r7 = mul_path_sen_list[1] + ', ' +  mul_path_sen_list[3] + ', ' +  mul_path_sen_list[5]
            mul_res_path_list = [r0, r1, r2, r3, r4, r5, r6, r7]
            print('MRP')
            print(mul_res_path_list)
            return mul_res_path_list


        for k, v in var_def_dict.items():
            # print(k)
            for v0 in v:
                
                if isinstance(v0, str):
                    continue
                
                # grep pre conditio node
                k_expr = self.convert_single_node_to_nl(v0, f, var_def_dict, var)
                print('kexpr ', k_expr)
                print(v0)
                
                pre_node_list, xor_node_list = self.find_control_flow(v0.node_id, f)
                for pn in pre_node_list:
                    
                    if pn.is_conditional():
                        # print('pre node ', pn, ' ', pn.type)
                        condition_sen = self.convert_single_node_to_nl(pn, f, var_def_dict, var)
                        print('cond sen ', condition_sen)
                       

                print(v0)
             

        if len(sv_list) == 0:
            return []

        
        if len(sv_list) > 1:
            sv_str = 'The variable ' + var.name + ' is related to state variable ' + ', '.join(sv_str_list[0:-1]) + ' and ' + sv_str_list[-1]
        if len(sv_list) == 1:
            sv_str = 'The variable ' + var.name + ' is related to state variable ' + sv_str_list[0]
        
        data_nl_list.append(sv_str)

       

        return ''.join(data_nl_list)

    


    def convert_single_node_to_nl(self, node: Node, f: Function, var_def_dict, amount_var):
        
        cmp_symbol_list = ['>', '<', '>=', '<=', '==']
        link_symbol_list = ['&&', '||']
        
        cmp_symbol_nl_dict = {'>': 'greater than', '<': 'less than', '>=': 'equal or greater than', '<=': 'equal or less than ', '==': 'equals to'}
        link_symbol_nl_dict = {'&&': 'and', '||': 'or'}
        var_def_dict[amount_var] = ['amount of token']
        var_name_def_dict = {}
        for k, v in var_def_dict.items():
            var_name_def_dict[k.name] = v
    
        nl_sentence = ''
        print(var_name_def_dict)

        node_expr = str(node.expression)
        if node.is_conditional:
            symbol_node_list = [lsymbol for lsymbol in link_symbol_list if lsymbol in str(node)]
            if len(symbol_node_list) == 0:
                for csymbol in cmp_symbol_list:
                    if csymbol in node_expr:
                        cmp_name = cmp_symbol_nl_dict[csymbol]
                        lft_var_name = node_expr.split(csymbol)[0].strip()
                        rht_var_name = node_expr.split(csymbol)[1].strip()

                        if '[' in str(lft_var_name):
                            lft_var_name = lft_var_name.split('[')[0].strip()
                            
                        if '[' in str(rht_var_name):
                            rht_var_name = rht_var_name.split('[')[0].strip()
                        
                        if lft_var_name not in var_def_dict:
                            continue

                        if lft_var_name in var_name_def_dict and isinstance(var_name_def_dict[lft_var_name][0], str):
                            print('lfn ', lft_var_name, ' ', var_name_def_dict[lft_var_name][0])
                            lft_var_name = var_name_def_dict[lft_var_name][0]
                                
                        if rht_var_name in var_name_def_dict and isinstance(var_name_def_dict[rht_var_name][0], str):
                            print('rhn ', rht_var_name, ' ', var_name_def_dict[rht_var_name][0])
                            rht_var_name = var_name_def_dict[rht_var_name][0]

                        cmp_sen = lft_var_name + ' ' + cmp_name + ' ' + rht_var_name
                        # print('no ls sym sen ', cmp_sen)
                        return cmp_sen

            for lsymbol in link_symbol_list:
                
                if lsymbol in str(node_expr):
                    node_list = node_expr.split(lsymbol)

                    lsymbol_name = link_symbol_nl_dict[lsymbol]
                    single_cond_list = []

                    cmp_sen_list = []

                    for each_condition_node in node_list:
                        cmp_node = [cmps for cmps in cmp_symbol_list if cmps in each_condition_node]
                        if len(cmp_node) == 0:
                            single_condition = each_condition_node
                            if '[' in str(single_condition):
                                var_name = single_condition.split('[')[0].strip()
                            
                            if var_name_def_dict[var_name] == [STATE_VARIABLE]:
                                single_cond_list.append(STATE_VARIABLE + ' is True')
                            else:
                                single_cond_list.append(var_name)


                        else:
                           
                            for csymbol in cmp_symbol_list:
                                if csymbol in each_condition_node:
                                    lft_var_name = each_condition_node.split(csymbol)[0].strip()
                                    rht_var_name = each_condition_node.split(csymbol)[1].strip()
                                    cmp_name = cmp_symbol_nl_dict[csymbol]
                                    
                                    
                                    if lft_var_name in var_name_def_dict and isinstance(var_name_def_dict[lft_var_name][0], str):
                                        lft_var_name = var_name_def_dict[lft_var_name][0]
                            
                                    if rht_var_name in var_name_def_dict and isinstance(var_name_def_dict[rht_var_name][0], str):
                                        rht_var_name = var_name_def_dict[rht_var_name][0]

                                    cmp_sen = lft_var_name + ' ' + cmp_name + ' ' + rht_var_name
                                    cmp_sen_list.append(cmp_sen)

                    # nl_sentence = ''.join(single_cond_list) +  + lsymbol_name + cmp_sen
                    # print('nl sen ', nl_sentence)
                    if len(single_cond_list) == 0 and lsymbol_name != '':
                        nl_sentence = cmp_sen_list[0] + ' ' + lsymbol_name + ' ' + cmp_sen_list[1]
                        # print('nl0 ', nl_sentence)  
                        
                    elif len(single_cond_list) != 0 and lsymbol_name != '':
                        nl_sentence = ''.join(single_cond_list) + ' ' + lsymbol_name + ' ' + cmp_sen
                        # print('nl1 ', nl_sentence)  
                    return nl_sentence
        
        
        arithmetic_symbol_list = ['+', '-', '*', '/', '=']
        arithmetic_symbol_name_dict = {'+': 'plus', '-': 'minus', '*': 'multiplies by', '/': 'divides by', '=': 'equals'}
        
        if '=' in node_expr:
            lft_var_name = node_expr.split('=')[0]
            rht_var_name = node_expr.split('=')[1]

            if '(' and ',' in rht_var_name:
                arg_list = node_expr.split('(')[1].split(')')[0].split(',')
                arg_name_list = []
                for arg in arg_list:
                    if len(arg) != 0:
                        arg_name_list.append(var_name_def_dict[arg.strip()][0])
                
                args_name = ', '.join(arg_name_list)  
                rht_var_name = 'api(' + args_name + ')'
                return lft_var_name + 'equals ' + rht_var_name

            rht_var_name_cp = rht_var_name
            sname_list = []

            for asymbol in arithmetic_symbol_list:
                if asymbol in node_expr:
                   
                    node_expr = node_expr.replace(asymbol,  arithmetic_symbol_name_dict[asymbol])

            node_meta_list = node_expr.split(' ')
            format_meta_str = ''
            for nm in node_meta_list:
                if len(nm) == 0:
                    format_meta_str += ' '
                elif '[' in nm:
                    fnm = nm.split('[')[0].strip() 
                    format_meta_str += fnm + ' '
                elif nm in var_name_def_dict and isinstance(var_name_def_dict[nm][0], str):
                    format_meta_str += var_name_def_dict[nm][0] + ' '
                else:
                    format_meta_str += nm + ' '
            return format_meta_str           
            # var_list = rht_var_name_cp.split('sycs')
            # var_sen = lft_var_name + ' equals '
            # for var in var_list:
            #     print('varr ', var)
            #     if '[' in rht_var_name:
            #         former_part = rht_var_name.split('[')[0].strip()
            #         var_name = former_part.strip()
                    
               

            #     elif var.strip() in var_name_def_dict and isinstance(var_name_def_dict[var.strip()][0], str):
            #         var_name = var_name_def_dict[var.strip()][0]
                   
            #     else:
            #         var_name = var.strip()
            #     if var_list.index(var) == 0:
            #         var_sen += var_name + ' '
            #     else:        
            #         var_sen += var_name + ' ' + sname_list[var_list.index(var)]
            #     print('var sen ', var_sen)

            

            
            
        return ''


    def find_all_defs(self, var, f: Function):
        node_list = f.nodes
        def_list = []
        for node in node_list:
            if var in node.variables_written:
                def_list.append(node)
        return def_list    

    def track_balance(self, from_addr, to_addr, c, f: Function):
        print(from_addr)
        print(to_addr)
        
        # dict for from/to addr as key, changed var as value
        from_addr_val_list = []
        to_addr_val_list = []

        for node in f.nodes:
            lft_expr = ''
            node_str = str(node)

            if '=' in node_str:
                lft_expr = node_str.split('=')[0]
                
                if self.to_addr(from_addr) in lft_expr:
                    from_addr_val_list.append(self.get_balance_changed_val(node_str))
                    
                if self.to_addr(to_addr) in lft_expr:
                    to_addr_val_list.append(self.get_balance_changed_val(node_str))
        print('from addr val')
        
        from_addr_val_sum = ''.join(from_addr_val_list).strip()
        print(from_addr_val_sum)
        print('nega ')
        nega_from_val = self.nega_formula(from_addr_val_sum)
        
        print('to addr val ')
        to_addr_val_sum = ''.join(to_addr_val_list).strip()
        # print(to_addr_val_sum)
        
        if nega_from_val != to_addr_val_sum:
            match_nl = 'The change in the balance of ' + str(from_addr) + ' does not equal the change in the balance of ' + str(to_addr)
            
        else:
            match_nl = 'The change in the balance of ' + str(from_addr) + ' equals the change in the balance of ' + str(to_addr)
            

        sum_nl = '\nThe balance of ' + str(from_addr) + ' has changed (' + from_addr_val_sum + ') and the balance of ' + str(to_addr) + ' has changed (' + to_addr_val_sum + ')'
        return match_nl + sum_nl

        

        
                
 

    def to_addr(self, addr):
        return '[' + str(addr) + ']'

    def nega_formula(self, aexpr: str):
        nega_str = ''
        for i in range(0, len(aexpr)):
            if aexpr[i] == '+':
                nega_str += '-'
            elif aexpr[i] == '-':
                nega_str += '+'  
            else:
                nega_str += aexpr[i]
        return nega_str

    # get +/- value in balance
    def get_balance_changed_val(self, node_str: str):
        if '+=' in node_str:
            return '+' + node_str.split('+=')[1]
        if '-=' in node_str:
            return '-' + node_str.split('-=')[1]       
        if '=' in node_str:
            lft_var = node_str.split('=')[0].replace('EXPRESSION', '').strip()
            print('lft var ', lft_var)
            rht_var = node_str.split('=')[1].replace(lft_var, '')
            return rht_var


    def convert_sc_var_to_nl(vname, arg_list):
        vname_nl_dict = {
            'msg.sender':'The person who is cerrently connecting with the contract',
            'msg.value': 'The amount of wei sent with a message to the contract'
        }

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
                        # if SCOPE in condition_sentence:
                        #     pre_part = condition_sentence.split(SCOPE)[0]
                        #     digit = condition_sentence.split(SCOPE)[1].split(' ')[0]
                        #     post_part = condition_sentence.split(SCOPE + digit)[1]
                        #     condition_sentence = pre_part + ' ' + post_part
                        #     print('cond ', condition_sentence)

                        condition_sentence_set.append(condition_sentence)
        return xor_node_list_set 


    def find_dirct_control_node(self, node_id: int, f: Function):
        cfg_str = self.slithir_cfg_to_dot_str(f)
        f_node_list = f.nodes
        
        graph = pydot.graph_from_dot_data(cfg_str)[0]
        node_dict = {}
        for node in graph.get_nodes():
            node_dict[node.get_name()] = node.obj_dict['attributes']

        print('node dict')
        print(node_dict)    
        for edge in graph.get_edges():
            if edge.get_destination() == str(node_id):
                print('find edge ', edge.get_source())
                print(node_dict[edge.get_source()])
                if 'IF' in node_dict[edge.get_source()]['label']:
                    print('is condition node')
        


  
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
