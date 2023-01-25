import networkx as nx
import pydot
from simplenlg import NPPhraseSpec
from simplenlg import NLGFactory
import simplenlg.framework
from simplenlg import Lexicon
from simplenlg.realiser import Realiser
from simplenlg import phrasespec
import simplenlg.features

DEMO_PATH = 'graph.cfg.gv'
amount0 = ''
transfer_cnt = 0
TRANSFER_EVENT = '0xDDF252AD1BE2C89B69C2B068FC378DAA952BA7F163C4A11628F55A4DF523B3EF'

dependency_list = set()

graph_list = []

flow_graph = []

public_ir_list = []



def track_transfer_api(fname):
    if not str(fname).endswith('dot'):
        return
    
    ir_list = get_ir_list(fname)
      
    amount0 = ''
    # print(ir_list)
    for i in range(len(ir_list)):

        if TRANSFER_EVENT in ir_list[i]:
            gap = 4
            from_arg_ir = ir_list[i + gap]
            to_arg_ir = ir_list[i + gap + 1]
            amount_arg_ir = ir_list[i + gap + 2]
            from_arg_dep_set = track_dataflow(ir_list, from_arg_ir)
            to_arg_dep_set = track_dataflow(ir_list, to_arg_ir)
            amount_arg_dep_set = track_dataflow(ir_list, amount_arg_ir)
            print('to arg')
            print(to_arg_dep_set)
           
            if from_arg_dep_set != None and 'first amount' in from_arg_dep_set:
                from_arg_dep_set = set()
                from_arg_dep_set.add('user input')

            if to_arg_dep_set != None and to_arg_dep_set != None and 'first amount' in to_arg_dep_set:
                to_arg_dep_set = set()
                to_arg_dep_set.add('user input')
            if amount_arg_dep_set != None and 'first amount' in amount_arg_dep_set:
                amount_arg_dep_set = set()
                amount_arg_dep_set.add('user input')
           
            construct_single_nlg(from_arg_dep_set, to_arg_dep_set, amount_arg_dep_set, fname)


        if '0x23B872DD' in ir_list[i]:
            print('find transferFrom api')
            from_arg_ir = ir_list[i + 1]
            to_arg_ir = ir_list[i + 2]
            amount_arg_ir = ir_list[i + 3]
            # print(from_arg_ir)
            # print(to_arg_ir)
            # print(amount_arg_ir)

            from_arg_dep_set = track_dataflow(ir_list, from_arg_ir)
            to_arg_dep_set = track_dataflow(ir_list, to_arg_ir)
            # print(amount_arg_ir)
            if 'JUMPI' in amount_arg_ir:
                continue
            amount0 = amount_arg_ir.split('=')[1].split('(')[1].split(')')[0]
            print('amount 0', amount0)
            flow_graph.append(ir_list[i])

            amount_arg_dep_set = track_dataflow(ir_list, amount_arg_ir)

            # print('from ')
            # print(from_arg_dep_set)

            # print('to')
            # print(to_arg_dep_set)

            # print('amount')
            # print(amount_arg_dep_set)
            construct_nlg(from_arg_dep_set, to_arg_dep_set, amount_arg_dep_set, fname)

        if '0xA9059CBB' in ir_list[i]:
            print('transfer 2 ')
            cnt = 0
            address_arg = ''
            amount_arg_set = set()
            flow_graph.append(ir_list[i])
            for j in range(i, len(ir_list)):
                # print(j)
                if 'SLOAD' in ir_list[j]:
                    # print('find sload')
                    if cnt == 0:
                        flow_graph.append(ir_list[j])
                        address_arg = 'a third-party address'
                        cnt += 1
                if 'DUP4' in ir_list[j]:
                    if cnt < 2:
                        amount_arg_set = track_dataflow(ir_list, ir_list[j])
                        print('transfer 2 amount ')
                        print(amount_arg_set)
                        # print('ir j')
                        # print(ir_list[j])
                        flow_graph.append(ir_list[j])
                        cnt += 1
            print('cnt ', str(transfer_cnt))
            if transfer_cnt > 1:            
                construct_transfer_nlg(address_arg, amount_arg_set, fname) 
            else:
                construct_transfer_single_nlg(address_arg, amount_arg_set, fname) 


def construct_single_nlg(from_dep_set, to_dep_set, amount_dep_set, fname):
    if check_null(from_dep_set, to_dep_set, amount_dep_set) and len(from_dep_set) == len(to_dep_set) == len(amount_dep_set) == 1:
        lexicon = Lexicon.getDefaultLexicon()
        nlgf = NLGFactory(lexicon)
        p = nlgf.createClause()
        p.setSubject('the contract')
        p.setVerb('transfer')
        p.setObject('a user input value from a user input address to another user input address')
        realiser = Realiser(lexicon)
        nlg = realiser.realise(p)
        print(nlg)

def check_null(arg_set0, arg_set1, arg_set2):
    return arg_set0 != None and arg_set1 != None and arg_set2 != None


def construct_nlg(from_dep_set, to_dep_set, amount_dep_set, fname):
    global transfer_cnt

    # subject = NLGFactory.createNounPhrase("contract")
    # cal_verb = NLGFactory.createNounPhrase("calculate")
    # amount_obj = NLGFactory.createNounPhrase("amount")

    # subject.addModifier("from" + str(from_dep_set[0]) + 'to' + to_dep_set[0])
    lexicon = Lexicon.getDefaultLexicon()
    nlgf = NLGFactory(lexicon)
    p = nlgf.createClause()
    p.setSubject('the contract')
    p.setVerb('calculate')

    p.setObject('an amount')


    pp = nlgf.createPrepositionPhrase()
    # pp.addComplement()
    
    # print('amt')
    # print(amount_dep_set)
    # print(transfer_cnt)
    for amt_dep in amount_dep_set:
        if transfer_cnt  == 0 and amt_dep == 'first amount':
            continue
        pp.addComplement('a ' + amt_dep)
    pp.setPreposition("using")

    p.addComplement(pp)

    c = nlgf.createCoordinatedPhrase()
    s2 = nlgf.createClause("the contract", "transfer", "this amount")
    pp2 = nlgf.createPrepositionPhrase()
    
    
    
    pp2.setPreposition("from a " + str(next(iter(from_dep_set))) + ' address ' + 'to another ' + next(iter(to_dep_set)) + ' address')

    c.addCoordinate(p)
    c.addCoordinate(s2)
    realiser = Realiser(lexicon)

    s2.setComplement(pp2)
    nlg = realiser.realiseSentence(c)
        # nlg1 = realiser.realiseSentence(s2)
    # print(nlg1)
    print(nlg)
    write_nlg_to_file(fname, nlg)
    # nlg0 = realiser.realiseSentence(p)
    # print(nlg0)

def write_nlg_to_file(fname, nlg: str):
    nlg_dir = 'nlg/'
    if len(nlg) != 0:
        print('nlg ', nlg)
        nlg_file = nlg_dir + fname.split('/')[-1].split('.')[0] + '.txt'
        print(nlg_file)
        with open(nlg_file, 'w') as f:
            f.write(nlg)

def construct_transfer_nlg(address_arg, amount_set, fname):
    global transfer_cnt
    lexicon = Lexicon.getDefaultLexicon()
    nlgf = NLGFactory(lexicon)
    p = nlgf.createClause()
    p.setSubject('the contract')
    p.setVerb('calculate')

    p.setObject('a second amount')
    pp = nlgf.createPrepositionPhrase()

    if 'first amount' in amount_set:
        pp.addComplement('the first amount')
    pp.setPreposition("using")

    p.addComplement(pp)
    
    c = nlgf.createCoordinatedPhrase()
    s2 = nlgf.createClause("the contract", "transfer", "this amount")
    pp2 = nlgf.createPrepositionPhrase()
    pp2.setPreposition('to ' + address_arg)
    transfer_cnt += 1

    c.addCoordinate(p)
    c.addCoordinate(s2)
    realiser = Realiser(lexicon)

    s2.setComplement(pp2)
    nlg = realiser.realiseSentence(c)
        # nlg1 = realiser.realiseSentence(s2)
    # print(nlg1)
    print(nlg)
    write_nlg_to_file(fname, nlg)

def construct_transfer_single_nlg(address_arg, amount_set, fname):
    global transfer_cnt
    lexicon = Lexicon.getDefaultLexicon()
    nlgf = NLGFactory(lexicon)
    p = nlgf.createClause()
    print('amount set ', amount_set)
    if amount_set != None and len(amount_set) == 1 and next(iter(amount_set)) == 'first amount':
        
        pp = nlgf.createPrepositionPhrase()
        pp.setPreposition("from a user to a user input address")
        realiser = Realiser(lexicon)
        s2 = nlgf.createClause("the contract", "transfer", "a user input amount")
        c = nlgf.createCoordinatedPhrase()
        
        c.addCoordinate(s2)
        c.addCoordinate(pp)
        nlg = realiser.realiseSentence(c)
        print('nlg ', nlg)
        write_nlg_to_file(fname, nlg)
        return 


    # p.setSubject('the contract')
    # p.setVerb('calculate')

    # p.setObject('a second amount')
    pp = nlgf.createPrepositionPhrase()

    if amount_set != None and 'first amount' in amount_set:
        pp.addComplement('the first amount')
    pp.setPreposition("using")

    p.addComplement(pp)
    
    c = nlgf.createCoordinatedPhrase()
    s2 = nlgf.createClause("the contract", "transfer", "this amount")
    pp2 = nlgf.createPrepositionPhrase()
    pp2.setPreposition('to ' + address_arg)
    transfer_cnt += 1

    c.addCoordinate(p)
    c.addCoordinate(s2)
    realiser = Realiser(lexicon)

    s2.setComplement(pp2)
    nlg = realiser.realiseSentence(c)
        # nlg1 = realiser.realiseSentence(s2)
    # print(nlg1)
    print(nlg)
    write_nlg_to_file(fname, nlg)

def track_dataflow(ir_list, ir):
    if '=' in ir:
        rht_ir = ir.split('=')[1]
        if '(' in rht_ir and ')' in rht_ir:
            rht_val = rht_ir.split('(')[1].split(')')[0]
            # print(rht_val)
            dep_set = set()
            val = find_def_value(ir_list, rht_val, dep_set)
            if dep_set == None:
                return set()
            return dep_set

def find_def_value(ir_list, rht_val, dep_set):
    # while 1:
    for ir in ir_list:
            if '=' in ir:
                left_val = ir.split('=')[0].split(':')[1].strip()
                if rht_val in left_val:
                    # print('left val ', left_val)
                    # print('rht val ', rht_val)

                    ir_rht_val = ir.split('=')[1]
                    if 'CALLDATALOAD' in ir_rht_val:
                        # print('break userr input ', ir_rht_val)
                        dep_set.add('user input')
                        graph_list.append(ir)
                        flow_graph.append(ir)

                        return 'user input'
                    if amount0 in ir_rht_val:
    
                        dep_set.add('first amount')
                        graph_list.append(ir)
                        # flow_graph.append(ir)
                        public_ir_list.append(ir)
     
                    if 'TIMESTAMP' in ir_rht_val:
                        # print('break timestamp ', ir_rht_val)
                        dep_set.add('timestamp')
                        graph_list.append(ir)
                        flow_graph.append(ir)
                        return 'timestamp'
                    # split source -> amount relationship
                    if '(' in ir_rht_val and ')' in ir_rht_val:
                        format_ir_rht_val = ir_rht_val.split('(')[1].split(')')[0]
                        if ',' in format_ir_rht_val:
                            val_set = [ir.strip() for ir in format_ir_rht_val.split(',')]
                            print(val_set)
                            for val in val_set:
                                print('val ', val)
                                print(ir)
                                
                                find_def_value(ir_list, val, dep_set)
                        else:
                            val = format_ir_rht_val
                            # print('single val ', val)
                            find_def_value(ir_list, val, dep_set)

def get_ir_list(fname):
    print('fname ', fname)
    graph = pydot.graph_from_dot_file(fname)[0]
    # print(graph)
    bb_ir_list = str(graph).split('subgraph global {')[1].split('}')[0].split('\n')
    # print(bb_ir_list)
    ir_list = []
    
    for bb_ir in bb_ir_list:
        # print('bbir ', bb_ir)
        if bb_ir == ''  or 'fontname=Courier, fontsize' in bb_ir:
            continue
        # print('bb_ir ', bb_ir)
        format_ir_list = bb_ir.split('"')[1].split('"')[0].split('\l')
        format_ir_list = [ir for ir in format_ir_list if ir != '']
        ir_list += format_ir_list

    return ir_list


# if __name__ == '__main__':
#     track_transfer_api(DEMO_PATH)

# track_transfer_api(
#     '/Users/py/github/octopus/graph/0x87c45d5e31c5d1d0cd2b2e2ab7f0b002b05b45fa.dot'
# )

import glob
import os

graph_list = glob.glob("graph/*.dot")
for graph in graph_list:
    track_transfer_api(graph)
    os.system('mv ' + graph + ' checked/')



seen = set()
seen_add = seen.add
flow_graph = [x for x in flow_graph if not (x in seen or seen_add(x))]

print(get_ir_list(DEMO_PATH))
def sort_ir(ir):
    id = 0
    ir_list = get_ir_list(DEMO_PATH)
    for ir_l in ir_list:
        if ir in ir_l:
            return id
        id += 1

    # print('ir ', ir, ' id ', id)
    return id

flow_graph.sort(key=sort_ir)
print(public_ir_list)

id = 0
dot_list = []
with open('graph_block.dot', 'w') as f:
    for line in flow_graph:
        dot_str = str(id) + '[label="' + line + '"]\n'
        dot_list.append(dot_str)
        id += 1
    
    f.writelines(line + '\n' for line in flow_graph)
print(dot_list)
print(public_ir_list)
with open('dataflow.dot', 'w') as f:
    f.writelines(dot_list)
# G = nx.Graph(nx.nx_pydot.read_dot(DEMO_PATH))
# graph = pydot.graph_from_dot_file(DEMO_PATH)[0]
# print(graph)
# print(graph.get_node_list())
# for node in graph.get_nodes():
#     attr = node.obj_dict['attributes']
#     print(attr)
#     label = nx.get_node_attributes(G, 'label')
#     print(label)
# labels = nx.get_node_attributes(G, 'node')
# print(labels)