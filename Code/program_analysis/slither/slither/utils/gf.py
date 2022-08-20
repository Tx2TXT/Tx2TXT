from cmath import exp
from re import X
import re
import pydot
import networkx as nx
from pprint import pprint

test_fname = '/Users/py/github/SANUS/slither/large_dapps/example.dot'
graph = pydot.graph_from_dot_file(test_fname)[0]

first_class_symbol_parse_dict = {
    '>=': 'is greater than or equal to', '<=': 'is less than or equal to', '==': 'equals to', '*': 'multiplies by'
    , '+=': 'increase by', '-=': 'decrease by', '/': 'divides by', '&&': 'and', '||': 'or', 
    'revert()': 'cancel all actions and revert', '!=': 'not equals to'
}
second_class_symbol_parse_dict = {'!': 'NOT', '>': 'is greater than', '<': 'is less than', '=': 'is set to', '+': 'plus', '-': 'minus'}

def get_cond_list():
    cond_list = []
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']

        if 'label' not in attr:
            continue
        label = attr['label']
        if 'Node Type: IF' in label and 'transferFrom' not in label:        
            cond_list.append(node.get_name())
    return cond_list

def track_from_terminate(terminate):
    
    order = depth_first_search(terminate)
    path_list = []
    for i in range(1, len(order) - 1):
        j = i + 1
        if int(order[i]) >= int(order[j]):
            return path_list
        else:
            path_list.append(order[i])  
    order = list(set(order))
    return order
    des = terminate
    path_list = [des]
    while des != '0':
        src = find_pre_node(des)
        des = src
        path_list.append(des)

    return [ele for ele in reversed(path_list)] 

def find_pre_node(des):
    pre_node_list = []
    
    for e in graph.get_edges():
        if e.get_destination() == des:
            pre_node_list.append( e.get_source())
    # print(pre_node_list)        
    if len(pre_node_list) == 1:
        # print('e ', e)
        return pre_node_list[0]
    else:
        imin = 100
        idx = ''
        for pre_node in pre_node_list:
            
            ival = abs(int(pre_node) - int(des))
            if ival < imin:
                imin = ival
                idx = pre_node

        return idx

def get_terminate_list():
    terminate_list = []

    last_name = ''
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']

        if 'label' not in attr:
            continue
        # print(attr)
        label = attr['label']
        if 'RETURN ' in label:        
            terminate_list.append(node.get_name())
        last_name = node.get_name()

    if len(terminate_list) == 0:
        terminate_list = [last_name]
    return terminate_list

def parse_path_list():
    parse_node_dict = parse_node_nl()
    path_list = trase_graph()
    print('pl')
    print(path_list)    
    nl_sen_list = []
    for path in path_list:
        nl_sen = ''
        for node in path:
            if node not in parse_node_dict.keys():
                continue
            description = parse_node_dict[node]
            
            if description != 'false' and description != 'true':
                if description.startswith('if'):
                    if nl_sen.endswith(', '):
                        nl_sen += 'and '
                    elif nl_sen.endswith('. '):
                        description = description[0].upper() + description[1:]
                    if description != '':
                        nl_sen += description + ', '
                elif nl_sen.endswith('.'):
                    description = description[0].upper() + description[1:] 
                else:
                    if description != '':
                        nl_sen += description + '. '
        
        nl_sen = nl_sen[0].upper() + nl_sen[1:]
        nl_sen_list.append(nl_sen)
        print(nl_sen)
        
        
        with open('openseaio_description.txt', 'w') as f:
            
            f.write('\n'.join(nl_sen_list)) 


def new_trase_graph():
    condition_list = get_cond_list()
    terminate_list = get_terminate_list()

    des = '0'
    path_list = [[des]]


    # while des not in terminate_list:
    #     if des not in condition_list:
    #         des_next = find_single_next(des)[0]
    #         for path in path_list:
    #             path.append(des_next)
    #             des = des_next
    #     else:
    #         des0 = find_single_next[0]
    #         des1 = find_single_next[1]



def find_single_next(des):
    next_list = []
    for e in graph.edges():
        if e.get_source() == des:
            next_list.append(e.get_destination())
    return next_list        


def trase_graph():
    condition_list = get_cond_list()
    terminate_list = get_terminate_list()
    print('ter', terminate_list)
     
    path_list = []
    for ter in terminate_list:
        path_list.append(track_from_terminate(ter))
    
    res_list = path_list.copy()
    for cond in condition_list:
        for path in path_list:
            if cond in path:
                res0, res1 = get_cond_res(cond)
                if res0 in path:
                    another_path = path.copy()
                    idx = another_path.index(res0)
                    another_path[idx] = res1
                    res_list.append(another_path)
                elif res1 in path:
                    another_path = path.copy()
                    idx = another_path.index(res1)
                    another_path[idx] = res0
                    res_list.append(another_path)

    return res_list

def get_cond_res(cond):
    edge_list = graph.get_edges()
    next_edge_list = get_next_edge(cond, edge_list)
    return next_edge_list[0], next_edge_list[1]

visited = []

node_list = []
for node in graph.get_nodes():
    node_list.append(node.get_name())

def depth_first_search(root):
    order = []

    def dfs(node_now):
        visited.append(node_now)
        order.append(node_now)
        for n in get_next_edge(node_now, graph.get_edges()):
            if n not in visited:
                dfs(n)
    if root:
        dfs(root)
    for node in node_list:
        if node not in visited:
            dfs(node)
    return order       

def get_next_edge(source, edge_list):
    next_edge_list = []
    for e in edge_list:
        if e.get_source() == source:
            next_edge_list.append(e.get_destination())

    return next_edge_list        

def parse_node_nl():
    parse_dict = {}
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']
        
        if 'label' not in attr:
            continue
        # print(attr)
        label = attr['label']

        if 'EXPRESSION:\n' in label:
            expr = label.split('EXPRESSION:\n')[1].split('IRs')[0].replace(
                '\n', '').strip()
            for k, v in first_class_symbol_parse_dict.items():
                expr = expr.replace(k, first_class_symbol_parse_dict[k])

            for k, v in second_class_symbol_parse_dict.items():
                expr = expr.replace(k, second_class_symbol_parse_dict[k])    
            
            if 'Node Type: IF' in label and 'transferFrom' not in label:        
                expr = 'if ' + expr 

            if 'transferFrom' in label:
                # print('111')
                print(label)
                arg_list = label.split('transferFrom(')[1].split(')')[0].split(',')
                from_addr, to_addr, amount = arg_list[0], arg_list[1], arg_list[2]
                expr = 'The contract transfers ' + amount + ' from ' + from_addr + ' to ' + to_addr  

            parse_dict[node.get_name()] = expr

    return parse_dict    
    
parse_path_list()