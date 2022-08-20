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




test_fname = '/Users/py/github/SANUS/slither/large_dapps/example.dot'
graph = pydot.graph_from_dot_file(test_fname)[0]
G = nx.nx_pydot.from_pydot(graph)
# print(G.nodes)

first_class_symbol_parse_dict = {
    '>=': 'be greater than or equal to', '<=': 'be less than or equal to', '==': 'be equal to', '*': 'multiplies by'
    , '+=': 'increase by', '-=': 'decrease by', '/': 'divide by', '&&': 'and', '||': 'or', 
    'revert()': 'cancel all actions and revert', '!=': 'be not equal to'
}
second_class_symbol_parse_dict = {'!': 'NOT', '>': 'be greater than', '<': 'be less than', '=': 'be set to', '+': 'plus', '-': 'minus'}


def traverse_graph(fname):
    G = get_graph(fname)
    # transfer_node_list = find_transfer_nodes(fname)
    # print(transfer_node_list)
    path_list = []
    path_list = nx.all_simple_paths(G, source='0', target='81')
    print('path')
    print((list(path_list)))
    # for transfer_id in transfer_node_list:
    #     for path in nx.all_simple_paths(G, source='0', target=transfer_id):
    #         # print(path)
    #         if len(path) != 0:
    #             path_list.append(path)
            
    # return path_list

def get_graph(fname):
    graph = pydot.graph_from_dot_file(fname)[0]
    G = nx.nx_pydot.from_pydot(graph)
    return G

traverse_graph(test_fname)