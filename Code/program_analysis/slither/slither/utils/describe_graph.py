from re import T
import pydot
import networkx as nx
from operator import mod, rshift
import simplenlg

from simplenlg.framework import *
from simplenlg.lexicon import *
from simplenlg.realiser.english import *
from simplenlg.phrasespec import *
from simplenlg.features import *


RETURN = 'return'


test_fname = '/Users/py/github/SANUS/slither/VeriSmart-benchmarks/benchmarks/zeus/017.sol-WavesEthereumSwap-moveToWaves(string,uint256).dot'
graph = pydot.graph_from_dot_file(test_fname)[0]
G = nx.nx_pydot.from_pydot(graph)
# print(G.nodes)

first_class_symbol_parse_dict = {
    '>=': 'be greater than or equal to', '<=': 'be less than or equal to', '==': 'be equal to', '*': 'multiplies by'
    , '+=': 'increase by', '-=': 'decrease by', '/': 'divide by', '&&': 'and', '||': 'or', 
    'revert()': 'cancel all actions and revert', '!=': 'be not equal to'
}
second_class_symbol_parse_dict = {'!': 'NOT', '>': 'be greater than', '<': 'be less than', '=': 'be set to', '+': 'plus', '-': 'minus'}

amount_dependency_dict = {}



def get_graph(fname):
    graph = pydot.graph_from_dot_file(fname)[0]
    G = nx.nx_pydot.from_pydot(graph)
    return G

def traverse_graph(fname):
    G = get_graph(fname)
    transfer_node_list = find_transfer_nodes(fname)
    # print(transfer_node_list)
    path_list = []
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

def find_return_nodes(fname):
    tr_node_list = []
    for node in graph.get_nodes():
        attr = node.obj_dict['attributes']
        if 'RETURN' in attr['label']:
            id = str(node).split('[')[0].strip()
            tr_node_list.append(id)
    
    return tr_node_list     

def get_cond_brs(fname, from_id, to_id):
    with open(fname, 'r') as f:
        dot_list = f.readlines()
    # print(dot_list)   
    for node in dot_list:    
        # print('from id: ', from_id)
        # print('to id: ', to_id)
        attr = node.strip()

        if '->' in attr:
            node_from_id = attr.split('->')[0]
            node_to_id = attr.split('->')[1].split('[label')[0]
           
            if node_from_id == str(from_id) and node_to_id == str(to_id):
                # print('find ', node_from_id, '->', node_to_id)
                if 'True' in attr:
                    return True
                else:
                    return False    
    
# def parse_node_nl(node, is_true_cond):
#     attr = node.obj_dict['attributes']
#     label = attr['label']
    
#     if 'IRS' in label:
#         expr = label.split('EXPRESSION:\n')[1].split('IRs')[0].replace(
#                 '\n', '').strip()
#     else:
#         expr = label.split('EXPRESSION:\n')[1].split("\"")[0].replace('\n', '').strip() 

#     # print('expr ', expr)
#     subject = ''
#     verb = ''
#     obj = ''
#     lexicon = Lexicon.getDefaultLexicon()
#     nlgFactory = NLGFactory(lexicon)
#     realiser = Realiser(lexicon)

#     if 'RETURN' in label:
#         return ''

#     if 'api' in expr:
#         lft_amt = expr.split('=')[0].strip()
#         rht_amt = expr.split('api(')[1].split(')')[0]

#         if '{' in lft_amt:
#             # print(lft_amt)
#             lft_arg_list = lft_amt.split('{')[1].split('}')[0].split(',')
#             # print(lft_arg_list)
#         else:
#             lft_arg_list = [lft_amt]    
#         for lft_amt in lft_arg_list:    
#             if lft_amt in amount_dependency_dict:
#                 dep_set = amount_dependency_dict[lft_amt]
#                 if ',' in rht_amt:
#                     arg_list = rht_amt.split(',')
#                     for arg in arg_list:
#                         dep_set.add(arg.strip())
#                 else:
#                     dep_set.add(rht_amt.strip())
#                 amount_dependency_dict[lft_amt] = dep_set      
#             else:
#                 dep_set = set()
#                 if ',' in rht_amt:
#                     arg_list = rht_amt.split(',')
#                     for arg in arg_list:
#                         dep_set.add(arg.strip())
#                 else:
#                     dep_set.add(rht_amt.strip())
#                 amount_dependency_dict[lft_amt] = dep_set
#         return ''   

#     output_sum = ''
#     if 'transferFrom' in expr and 'call' not in expr:
#         for k, v in amount_dependency_dict.items():
#             subject = 'the function'
#             verb = 'calculate'
#             obj = k + ' using ' + ', '.join(v)
#             nlg_sen0 = nlgFactory.createClause(subject, verb, obj)
#             output0 = realiser.realiseSentence(nlg_sen0)
#             output_sum += output0
           
#         arg_list = expr.split('transferFrom(')[1].split(')')[0].split(',')
#         from_addr, to_addr, amount = arg_list[0].strip(), arg_list[1].strip(), arg_list[2].strip()
#         subject = 'the contract'
#         verb = 'transfer'
#         obj =  amount + ' from ' + from_addr + ' to ' + to_addr
#         nlg_sen = nlgFactory.createClause(subject, verb, obj)
#         output = realiser.realiseSentence(nlg_sen)
#         return output_sum + output
#     elif 'transfer' in expr and 'call' not in expr:
#         for k, v in amount_dependency_dict.items():
#             subject = 'the function'
#             verb = 'calculate'
#             obj = k + ' using ' + ', '.join(v)
#             nlg_sen0 = nlgFactory.createClause(subject, verb, obj)
#             output0 = realiser.realiseSentence(nlg_sen0)
#             output_sum += output0
           
#         # print('transfer label ', expr)
#         arg_list = expr.split('transfer(')[1].split(')')[0].split(',')
#         amount = arg_list[0].strip()
#         to_addr = arg_list[1].strip()
#         subject = 'the contract'
#         verb = 'transfer'
#         obj = amount + ' to ' + to_addr
#         nlg_sen = nlgFactory.createClause(subject, verb, obj)
#         output = realiser.realiseSentence(nlg_sen)
#         return output_sum + output
#     elif 'call transfer' in expr:
#         return ''   

#     if_str = ''
#     # print(label, ' ', 'IF' in label)
#     if 'IF' in label:
#         if is_true_cond:
#             if_str = 'if '
#         else:
#             if_str = 'if not '    
#     if is_true_cond == None:
#         if_str = ''

   
#     first_k = False
#     for k, v in first_class_symbol_parse_dict.items():
#         if k in expr and not first_k:
#             # print(k, ' ', expr)
#             # expr = expr.replace(k, first_class_symbol_parse_dict[k])
            
#             subject = if_str + expr.split(k)[0].strip()
#             if '{' in subject:
#                 subject = 'amount'
#             verb = first_class_symbol_parse_dict[k]
#             obj = expr.split(k)[1].strip()
#             first_k = True
#             # print('first k ', k , ' ', first_k)

#     if not first_k:        
#         for k, v in second_class_symbol_parse_dict.items():
#             if k in expr:
#                 # print('EXPR: ', expr)
#                 # expr = expr.replace(k, second_class_symbol_parse_dict[k])  
#                 subject = if_str + expr.split(k)[0].strip()
#                 if '{' in subject:
#                     subject = 'amount'
#                 verb = second_class_symbol_parse_dict[k]
#                 obj = expr.split(k)[1].strip()

#     nlg_sen = nlgFactory.createClause(subject, verb, obj)
#     output = realiser.realiseSentence(nlg_sen)

#     return output

def get_node_clause(node, is_true_cond):
    attr = node.obj_dict['attributes']
    label = attr['label']

    # parse single ir expression
    if 'IRS' in label:
        expr = label.split('EXPRESSION:\n')[1].split('IRs')[0].replace(
                '\n', '').strip()
    else:
        expr = label.split('EXPRESSION:\n')[1].split("\"")[0].replace('\n', '').strip() 

    subject = ''
    verb = ''
    obj = ''
    lexicon = Lexicon.getDefaultLexicon()
    nlgFactory = NLGFactory(lexicon)

    if RETURN in label:
        return None

    if 'api' in expr:
        lft_amt = expr.split('=')[0].strip()
        rht_amt = expr.split('api(')[1].split(')')[0]

        if '{' in lft_amt:
            # print(lft_amt)
            lft_arg_list = lft_amt.split('{')[1].split('}')[0].split(',')
            # print(lft_arg_list)
        else:
            lft_arg_list = [lft_amt]    
        for lft_amt in lft_arg_list:    
            if lft_amt in amount_dependency_dict:
                dep_set = amount_dependency_dict[lft_amt]
                if ',' in rht_amt:
                    arg_list = rht_amt.split(',')
                    for arg in arg_list:
                        dep_set.add(arg.strip())
                else:
                    dep_set.add(rht_amt.strip())
                amount_dependency_dict[lft_amt] = dep_set      
            else:
                dep_set = set()
                if ',' in rht_amt:
                    arg_list = rht_amt.split(',')
                    for arg in arg_list:
                        dep_set.add(arg.strip())
                else:
                    dep_set.add(rht_amt.strip())
                amount_dependency_dict[lft_amt] = dep_set
        

def parse_node_nl(node, is_true_cond):
    cset = []
    attr = node.obj_dict['attributes']
    label = attr['label']
    if 'Node Type: ENTRY_POINT 0' in label:
        return []
    
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
    
    if 'RETURN' in label:
        return []

    if 'api' in expr:
        lft_amt = expr.split('=')[0].strip()
        rht_amt = expr.split('api(')[1].split(')')[0]

        if '{' in lft_amt:
            lft_arg_list = lft_amt.split('{')[1].split('}')[0].split(',')
        else:
            lft_arg_list = [lft_amt]    
        for lft_amt in lft_arg_list:    
            if lft_amt in amount_dependency_dict:
                dep_set = amount_dependency_dict[lft_amt]
                if ',' in rht_amt:
                    arg_list = rht_amt.split(',')
                    for arg in arg_list:
                        dep_set.add(arg.strip())
                else:
                    dep_set.add(rht_amt.strip())
                # amount_dependency_dict[lft_amt] = dep_set
                subject = 'the function'
                verb = 'calculate'
                obj = lft_amt + ' using ' + ', '.join(dep_set)
                cla = nlgFactory.createClause(subject, verb, obj)
                cset.append(cla)
            else:
                dep_set = set()
                if ',' in rht_amt:
                    arg_list = rht_amt.split(',')
                    for arg in arg_list:
                        dep_set.add(arg.strip())
                else:
                    dep_set.add(rht_amt.strip())
                # amount_dependency_dict[lft_amt] = dep_set
                subject = 'the function'
                verb = 'calculate'
                obj = lft_amt + ' using ' + ', '.join(dep_set)
                cla = nlgFactory.createClause(subject, verb, obj)
                cset.append(cla)
        return cset    

    if 'transferFrom' in expr and 'call' not in expr:
        for k, v in amount_dependency_dict.items():
            subject = 'the function'
            verb = 'calculate'
            obj = k + ' using ' + ', '.join(v)
            nlg_sen0 = nlgFactory.createClause(subject, verb, obj)
            # output0 = realiser.realiseSentence(nlg_sen0)
            # output_sum += output0
            # c = nlgFactory.createCoordinatedPhrase()
            # for sp in sp_list:
            #     c.addCoordinate(sp)
            # c.addCoordinate(nlg_sen)
            # output = realiser.realiseSentence(c)
            cset.append(nlg_sen0)
           
        arg_list = expr.split('transferFrom(')[1].split(')')[0].split(',')
        from_addr, to_addr, amount = arg_list[0].strip(), arg_list[1].strip(), arg_list[2].strip()
        subject = 'the contract'
        verb = 'transfer'
        obj =  amount + ' from ' + from_addr + ' to ' + to_addr
        nlg_sen = nlgFactory.createClause(subject, verb, obj)
        # output = realiser.realiseSentence(nlg_sen)
        cset.append(nlg_sen)
        return cset
    elif 'transfer' in expr and 'call' not in expr:
        # for k, v in amount_dependency_dict.items():
        #     subject = 'the function'
        #     verb = 'calculate'
        #     obj = k + ' using ' + ', '.join(v)
        #     nlg_sen0 = nlgFactory.createClause(subject, verb, obj)
        #     # output0 = realiser.realiseSentence(nlg_sen0)
        #     # output_sum += output0
        #     cset.append(nlg_sen0)
        #     return cset

           
        # print('transfer label ', expr)
        arg_list = expr.split('transfer(')[1].split(')')[0].split(',')
        amount = arg_list[1].strip()
        to_addr = arg_list[0].strip()
        subject = 'the contract'
        verb = 'transfer'
        obj = amount + ' to ' + to_addr
        nlg_sen = nlgFactory.createClause(subject, verb, obj)
        cset.append(nlg_sen)
        return cset
    elif 'call transfer' in expr:
        return []   

    if_str = ''
    # print(label, ' ', 'IF' in label)
    if 'IF' in label:
        if is_true_cond:
            if_str = 'if '
        else:
            if_str = 'if not '    
    if is_true_cond == None:
        if_str = ''

   
    first_k = False
    for k, v in first_class_symbol_parse_dict.items():
        if k in expr and not first_k:
                        
            subject = if_str + expr.split(k)[0].strip()
            if '{' in subject and is_true_cond != None:
                subject = 'if amount'
            if '{' in subject and is_true_cond == None:
                subject = 'if amount'
            verb = first_class_symbol_parse_dict[k]
            obj = expr.split(k)[1].strip()
            first_k = True
            # print('first k ', k , ' ', first_k)

    if not first_k:        
        for k, v in second_class_symbol_parse_dict.items():
            if k in expr:
                subject = if_str + expr.split(k)[0].strip()
                if '{' in subject and is_true_cond != None:
                    subject = 'if amount'
                if '{' in subject and is_true_cond == None:
                    subject = 'if amount'
                verb = second_class_symbol_parse_dict[k]
                obj = expr.split(k)[1].strip()

    nlg_sen = nlgFactory.createClause(subject, verb, obj)
    cset.append(nlg_sen)
    return cset
    # output = realiser.realiseSentence(nlg_sen)

    # return output    

path_list = traverse_graph(test_fname)
node_list = graph.get_nodes()
# for node in node_list:
#     print(node)
condition_node_list = find_condition_nodes(test_fname)
return_node_list = find_return_nodes(test_fname)
# print(path_list)

# for node in node_list:
#     print('node ', node, ' ', type(node))
    
# for node in node_list:
#     print(node, ' ', node['label'])
lexicon = Lexicon.getDefaultLexicon()
nlgFactory = NLGFactory(lexicon)
c = nlgFactory.createCoordinatedPhrase()

print('cond ', condition_node_list)

for path in path_list:
    nlg_sen_list = ''

    
    for i in range(0, len(path)):
        nid = path[i]
        # print('nid ', nid)
        n = node_list[int(nid)]
        
        if nid in condition_node_list:
           
            if i + 1 > len(path) - 1:
                continue
            tf_br_id = path[i + 1]
            
            tf_node = node_list[int(tf_br_id)]
            attr = tf_node.obj_dict['attributes']
            tf_node_label = attr['label']

            from_id = i
            to_id = i + 1
            is_true_cond = get_cond_brs(test_fname, from_id, to_id)  
            
            n = node_list[int(nid)]
            nlg_sen_set = parse_node_nl(n, is_true_cond)
            if len(nlg_sen_set) != 0:
                for nl in nlg_sen_set:
                    c.addCoordinate(nl)         
                
        elif nid not in condition_node_list and nid not in return_node_list:
            realiser = Realiser(lexicon)
            nlg_sen = parse_node_nl(n, None) 
            # print(nlg_sen)
            for nl in nlg_sen:
                c.addCoordinate(nl)
                
            output = realiser.realiseSentence(c)
            # print('expr ', nlg_sen)
            nlg_sen_list += output
            c = nlgFactory.createCoordinatedPhrase()

    print(nlg_sen_list)
