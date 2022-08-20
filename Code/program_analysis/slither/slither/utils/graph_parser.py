from re import T
import pydot
import networkx as nx
from operator import le, mod, rshift
import simplenlg
import graph_parser1

from simplenlg.framework import *
from simplenlg.lexicon import *
from simplenlg.realiser.english import *
from simplenlg.phrasespec import *
from simplenlg.features import *




test_fname = '/Users/py/github/SANUS/slither/large_dapps/example_symbol.dot'
graph = pydot.graph_from_dot_file(test_fname)[0]
G = nx.nx_pydot.from_pydot(graph)
# print(G.nodes)

first_class_symbol_parse_dict = {
    '>=': 'be greater than or equal to', '<=': 'be less than or equal to', '==': 'be equal to', '*': 'multiplies by'
    , '+=': 'increase by', '-=': 'decrease by', '/': 'divide by', '&&': 'and', '||': 'or', 
    'revert()': 'cancel all actions and revert', '!=': 'be not equal to'
}
second_class_symbol_parse_dict = {'!': 'NOT', '>': 'be greater than', '<': 'be less than', '=': 'be set to', '+': 'plus', '-': 'minus'}



def get_graph(fname):
    graph = pydot.graph_from_dot_file(fname)[0]
    G = nx.nx_pydot.from_pydot(graph)
    return G

def traverse_graph(fname):
    G = get_graph(fname)
    transfer_node_list = find_transfer_nodes(fname)
    # print(transfer_node_list)
    path_list = []
    # path_list = nx.all_simple_paths(G, source='0', target='80')
    # print('path')
    # print(path_list)
    for transfer_id in transfer_node_list:
        for path in nx.all_simple_paths(G, source='0', target=transfer_id):
            # print(path)
            if len(path) != 0:
                path_list.append(path)
            
    return path_list


def find_transfer_nodes(fname):
    tr_node_list = []
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']
        if 'transfer' in attr['label']:
            id = str(node).split('[')[0].strip()
            tr_node_list.append(id)
    
    return tr_node_list        

def find_condition_nodes(fname):
    tr_node_list = []
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']
        if 'IF' in attr['label']:
            id = str(node).split('[')[0].strip()
            tr_node_list.append(id)
    
    return tr_node_list 

dependency_dict = {}

amount_var_dict = {}
def parse_node_nl(node, is_true_cond):
    attr = node.obj_dict['attributes']
    label = attr['label']
    # print('label ', label)

    # print('label ', label)
    if 'IRS' in label:
        expr = label.split('EXPRESSION:\n')[1].split('IRs')[0].replace(
                '\n', '').strip()
    else:
        expr = label.split('EXPRESSION:\n')[1].split("\"")[0].replace('\n', '').strip() 

    # print('expr ', expr)
    subject = ''
    verb = ''
    obj = ''
    lexicon = Lexicon.getDefaultLexicon()
    nlgFactory = NLGFactory(lexicon)
    realiser = Realiser(lexicon)
    output = ''

    transfer_idx = 0

    if 'RETURN' in label:
        return ''

    if 'transferFrom' in expr and 'call' not in expr:
        tid = 'amount' + str(transfer_idx)
        subject = 'the function'
        verb = 'calculate'
        obj = tid 
        mer = ' using '

        dep_list = amount_var_dict[tid]
        if int(transfer_idx) == 0:
            print(amount_var_dict)
            if 'user input value 0' in dep_list:
                mer += 'a user input'
            if 'timestamp' in dep_list:
                mer += ' and a timestamp'  

        if int(transfer_idx) >= 1:
            dep_list = amount_var_dict[tid]
            if len(dep_list) == 1 and dep_list[0] == 'amount0':
                mer += ' the first amount'   
        nlg_sen = nlgFactory.createClause(subject, verb, obj + mer) 
        output = realiser.realiseSentence(nlg_sen)
        print('obj ', obj + mer)

        print(output)     
        # else:
        #     if 'amount0'

                # print('111')
        arg_list = expr.split('transferFrom(')[1].split(')')[0].split(',')
        from_addr, to_addr, amount = arg_list[0].strip(), arg_list[1].strip(), arg_list[2].strip()
        verb = 'transfer'
        obj =  amount + ' from ' + from_addr + ' to ' + to_addr
        nlg_sen = nlgFactory.createClause(subject, verb, obj)
        output = realiser.realiseSentence(nlg_sen)
        transfer_idx += 1
        return output

    elif 'transfer' in expr:
        arg_list = expr.split('transfer(')[1].split(')')[0].split(',')
        amount = arg_list[0].strip()
        to_addr = arg_list[1].strip()
        subject = 'the contract'
        verb = 'transfer'
        obj = amount + ' to ' + to_addr
        nlg_sen = nlgFactory.createClause(subject, verb, obj)
        output = realiser.realiseSentence(nlg_sen)
        transfer_idx += 1

        return output

    if_str = ''


    if 'IF' in label:
        if is_true_cond:
            if_str = 'if'
        else:
            if_str = 'if not '    
    if is_true_cond == None:
        if_str = ''

    if 'amount' and '=' in expr:
        lft_expr = expr.split('=')[0].strip()
        rht_expr = expr.split('=')[1].strip()
        if '{' in lft_expr:
            amount_list = [amt.strip() for amt in lft_expr.split('{')[1].split('}')[0].split(',')]
            # print(amount_list)
            if 'api' in rht_expr:
                dep_list = rht_expr.split('(')[1].split(')')[0].strip()
               
                if ',' not in dep_list:
                    for amt in amount_list:
                        if amt not in amount_var_dict:
                            init_set = set()
                            init_set.add(dep_list)
                            amount_var_dict[amt] = init_set
                        else:
                            to_up_set = amount_var_dict[amt]
                            to_up_set.add(dep_list)
                            amount_var_dict[amt] = to_up_set
                else:
                    dep_seq = dep_list.split(',')
                    for amt in amount_list:
                        if amt not in amount_var_dict:
                            init_set = set()
                            init_set.add(dep_list)
                            amount_var_dict[amt] = init_set
                        else:
                            to_up_set = amount_var_dict[amt]
                            to_up_set.add(dep_list)
                            amount_var_dict[amt] = to_up_set
        
        else:
             if 'api' and 'amount' in rht_expr:
                amount_var_dict[lft_expr] = rht_expr.split('api(')[1].split(')')[0].strip()


        # print(amount_var_dict)


        
        # subj = 'function'
        # verb = 'calculate'

    # print    

   
    # first_k = False
    # for k, v in first_class_symbol_parse_dict.items():
    #     if k in expr and not first_k:
    #         # print(k, ' ', expr)
    #         # expr = expr.replace(k, first_class_symbol_parse_dict[k])
            
    #         subject = if_str + expr.split(k)[0].strip()
    #         if '{' in subject:
    #             subject = 'the function'
    #         verb = first_class_symbol_parse_dict[k]
    #         obj0 = expr.split(k)[1].strip()
    #         print('obj0 ', obj0)
    #         if '(' in obj0 and ',' in obj0:
    #             objs = obj.split('(')[1].split(')')[0]
    #             for ob in objs:
    #                 obj = ob + ' and '
    #         if '(' in obj0 and ',' not in obj0:
    #             obj = obj.split('(')[1].split(')')[0]
                    
                
    #         first_k = True
    #         # print('first k ', k , ' ', first_k)

    # if not first_k:        
    #     for k, v in second_class_symbol_parse_dict.items():
    #         if k in expr:
    #             # print('EXPR: ', expr)
    #             # expr = expr.replace(k, second_class_symbol_parse_dict[k])  
    #             subject = if_str + expr.split(k)[0].strip()
    #             if '{' in subject:
    #                 subject = 'the function'
    #             verb = second_class_symbol_parse_dict[k]
    #             obj0 = expr.split(k)[1].strip()
    #             print('obj0 ', obj0)
    #             if '(' in obj0 and ',' in obj0:
    #                 objs = obj0.split('(')[1].split(')')[0]
    #                 for ob in objs:
    #                     obj = ob + ' and '
    #             if '(' in obj0 and ',' not in obj0:
    #                 obj = obj0.split('(')[1].split(')')[0]

    # nlg_sen = nlgFactory.createClause(subject, verb, obj)
    # output = realiser.realiseSentence(nlg_sen)

    
    return output

import time
start = time.time()

path_list = traverse_graph(test_fname)
node_list = graph.get_nodes()
# for node in node_list:
#     print(node)
condition_node_list = find_condition_nodes(test_fname)
# print(path_list)

# for node in node_list:
#     print('node ', node, ' ', type(node))
    
# for node in node_list:
#     print(node, ' ', node['label'])


for path in path_list:
    print(path)
    nlg_sen_list = ''
    for i in range(0, len(path)):
        nid = path[i]
        # print('nid ', nid)
        n = node_list[int(nid)]
        if nid in condition_node_list:
            tf_br_id = path[i + 1]
            tf_node = node_list[int(tf_br_id)]
            attr = tf_node.obj_dict['attributes']
            tf_node_label = attr['label']

            if 'True' in tf_node_label:
                is_true_cond = True
            else:
                is_true_cond = False    
            
            n = node_list[int(nid)]

            nlg_sen = parse_node_nl(n, is_true_cond)
            # print('cond ', nlg_sen)
        else:
            nlg_sen = parse_node_nl(n, None) 
            # print('expr ', nlg_sen)

        nlg_sen_list += nlg_sen
    print(nlg_sen_list)
end = time.time()
print('total cost ' , str(end - start))








