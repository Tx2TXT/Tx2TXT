import networkx as nx
import pydot
import constants

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

label_ir_list = []
arrow_list = []

id = 0


class CTAnalysis:
    def __init__(self, fname) -> None:
        self.fname = fname
        self.bb_ir_list = self.get_ir_list()[1]
        self.ir_list = self.get_ir_list()[0]
        self.id = 0
        self.first_amount = ''
        self.transfer_num = 0
        self.first_transfer_reg = ''

    def find_lowlevel_transfer(self):
        for ir in self.ir_list:
            if constants.lowlevel_call in ir:
                wei_reg = ir.split(',')[2].strip()
                wei_depset = set()
                wei_ir_list = []
                self.find_definition(wei_reg, wei_depset, wei_ir_list)
                print('def of wei ', wei_reg)

                to_reg = ir.split(',')[1].strip()
                to_depset = set()
                to_ir_list = []

                self.find_definition(to_reg, to_depset, to_ir_list)
                print('def of to ', to_reg)
                print(to_depset)

                lowlevel_nlg = self.construct_lowlevel_nlg(to_depset, wei_depset)

                with open(constants.llnlg + self.fname.split('graph/')[1] + '.txt', 'a+') as f:
                    f.write(lowlevel_nlg)

    def find_transfer_call(self):
        for ir in self.ir_list:
            if constants.transfer_from in ir:
                print('find transfer from ')
                mstore_ir_list = self.find_next_n_mstore(ir, 4)
                self.transfer_num += 1
                print(mstore_ir_list)

                from_mstore_ir = mstore_ir_list[0]
                to_mstore_ir = mstore_ir_list[1]
                amount_mstore_ir = mstore_ir_list[2]

                if self.transfer_num == 1:  # first transfer
                    transfer_reg = self.get_mstore_value(amount_mstore_ir)
                    self.first_transfer_reg = transfer_reg

                from_dep_set, from_flow_list = self.get_depset_flow(from_mstore_ir)
                to_dep_set, to_flow_list = self.get_depset_flow(to_mstore_ir)
                amount_dep_set, amount_flow_list = self.get_depset_flow(amount_mstore_ir)

                if len(from_dep_set) == 0:
                    from_dep_set.add(constants.user_input_addr)

                if len(to_dep_set) == 0:
                    to_dep_set.add(constants.user_input_addr)

                self.construct_nlg(from_dep_set, to_dep_set, amount_dep_set)

                transfer_call = self.find_call(self.ir_list.index(ir))
                call_label = str(self.id) + constants.SP + \
                             constants.lft_label_brkt + transfer_call + constants.rht_label_brkt
                label_ir_list.append(call_label)
                transfer_call_id = self.id

                self.construct_dot(from_flow_list, transfer_call_id)
                self.construct_dot(to_flow_list, transfer_call_id)
                self.construct_dot(amount_flow_list, transfer_call_id)
                print(from_dep_set)
                print(to_dep_set)
                print(amount_dep_set)

        self.write_graph(label_ir_list, arrow_list)

    def construct_lowlevel_nlg(self, to_depset, amount_depset):
        lexicon = Lexicon.getDefaultLexicon()
        nlg = NLGFactory(lexicon)
        p = nlg.createClause()
        p.setSubject('The contract')
        p.setVerb('transfer')

        to_addr = next(iter(to_depset))

        if to_addr == constants.state_var:
            to_addr = constants.state_var_addr
        elif to_addr == '':
            to_addr = constants.user


        if constants.balance in amount_depset:
            p.setObject('the balance of contract to ' + to_addr)
        elif len(amount_depset) != 0:
            amount_str = next(iter(amount_depset))
            p.setObject(amount_str + to_addr)
        elif len(amount_depset) == 0:
            p.setObject('the balance of contract to ' + to_addr)

        realiser = Realiser(lexicon)
        nlg_sen = realiser.realiseSentence(p)
        return nlg_sen + '\n'

    def construct_nlg(self, from_depset, to_depset, amount_depset):
        lexicon = Lexicon.getDefaultLexicon()
        nlgf = NLGFactory(lexicon)
        p = nlgf.createClause()
        p.setSubject('The contract')
        realiser = Realiser(lexicon)
        # p.setVerb('transfer')
        from_str = next(iter(from_depset))
        to_str = next(iter(to_depset))
        if self.transfer_num == 1:
            if len(amount_depset) > 1:
                p.setVerb('calculate')
                obj_str = 'an amount using '
                for amt_dep in amount_depset:
                    obj_str += amt_dep + ' and '
                obj_str = obj_str[0:-5]
                p.setObject(obj_str)
                nlg = realiser.realiseSentence(p)
                p2 = nlgf.createClause()
                p2.setSubject('Then the contract')
                p2.setVerb('transfer')

                if from_str == constants.user_input:
                    from_str = constants.user_input_addr
                if to_str == constants.user_input:
                    to_str = constants.user_input_addr2
                p2.setObject('this amount from ' + from_str + ' to ' + to_str)

                nlg1 = realiser.realiseSentence(p2)
                sum_nlg = nlg + constants.lb + nlg1 + constants.lb
                with open(constants.nlg + self.fname.split('.cfg.gv')[0] + '.txt', 'a+') as f:
                    f.write(sum_nlg)

        if 'amount0' in amount_depset:
            p.setVerb('calculate')
            obj_str = 'an amount using a first amount'
            p.setObject(obj_str)
            realiser = Realiser(lexicon)
            nlg = realiser.realiseSentence(p)
            # print(nlg)
            p2 = nlgf.createClause()
            p2.setSubject('Then the contract')
            p2.setVerb('transfer')

            if from_str == constants.user_input:
                from_str = constants.user_input_addr

            if to_str == constants.user_input:
                to_str = constants.user_input_addr2

            if to_str == constants.state_var:
                to_str += ' address '
            p2.setObject('this amount from ' + from_str + ' to ' + to_str)

            nlg1 = realiser.realiseSentence(p2)
            # print(nlg1)
            nlg += constants.lb + nlg1 + constants.lb
            with open(constants.nlg + self.fname.split('.cfg.gv')[0] + '.txt', 'a+') as f:
                f.write(nlg)
            # print(nlg)

        elif len(amount_depset) == 1:
            amount_str = next(iter(amount_depset))
            p.setVerb('transfer')
            if to_str == constants.state_var:
                to_str = constants.state_var_addr

            if from_str == constants.user_input:
                from_str = constants.user_input_addr

            if to_str == constants.user_input:
                to_str = constants.user_input_addr2

            p.setObject(amount_str + ' from ' + from_str + ' to ' + to_str)

            nlg = realiser.realiseSentence(p)
            # print(nlg)
            nlg += constants.lb
            with open(constants.nlg + self.fname.split('.cfg.gv')[0] + '.txt', 'a+') as f:
                f.write(nlg)

    def write_graph(self, label_ir_list, arrow_list):
        graph_name = self.fname.split('.cfg.gv')[0] + '.dot'
        header = 'digraph "graph.cfg.gv" {\nsubgraph global {\n'
        tail = '}\n}'
        with open(graph_name, 'a+') as f:
            f.write(header)
            for li in label_ir_list:
                f.write(li + '\n')
            for aw in arrow_list:
                f.write(aw + '\n')
            f.write(tail)

    def construct_dot(self, from_flow_list, transfer_call_id):
        # start_id = self.id
        temp_id = self.id + 1
        temp_arrow = str(temp_id) + constants.arrow + str(transfer_call_id) + constants.split
        arrow_list.append(temp_arrow)

        for i in range(len(from_flow_list)):
            self.id += 1

            fflow_ir = str(self.id) + constants.SP + \
                       constants.lft_label_brkt + from_flow_list[i] + constants.rht_label_brkt
            label_ir_list.append(fflow_ir)
            if i == len(from_flow_list) - 1:
                continue
            else:
                flow_label = str(self.id + 1) + constants.arrow + str(self.id) + constants.split
                arrow_list.append(flow_label)

        return label_ir_list, arrow_list

    def find_call(self, transfer_sig_idx):
        ir_list = self.ir_list
        for i in range(transfer_sig_idx, len(ir_list)):
            if constants.call in ir_list[i]:
                return ir_list[i]

    def get_depset_flow(self, mstore_ir):
        mstore_val = self.get_mstore_value(mstore_ir)
        dep_set = set()
        ir_list = []
        self.find_definition(mstore_val.strip(), dep_set, ir_list)
        return dep_set, ir_list

    def find_definition(self, val_reg, dep_set, ir_list):
        for ir in self.ir_list:
            if '=' in ir:
                ir_lft_val = ir.split('=')[0].strip()
                # print(ir_lft_val)
                if val_reg == ir_lft_val:
                    ir_rht_val = ir.split('=')[1]

                    if ',' in ir_rht_val:
                        rht_val0 = ir_rht_val.split('(')[1].split(',')[0].strip()
                        rht_val1 = ir_rht_val.split(')')[0].split(',')[1].strip()
                        if self.transfer_num > 1 and (
                                self.first_transfer_reg in rht_val0 or self.first_transfer_reg in rht_val1):
                            # print('match first amount')
                            dep_set.add('amount0')

                        if constants.calldataload in rht_val0 or constants.calldataload in rht_val1:
                            dep_set.add(constants.user_input)
                            ir_list.append(ir)
                            return constants.user_input
                        if constants.sload in rht_val0 or constants.calldataload in rht_val1:
                            dep_set.add(constants.state_var)
                            ir_list.append(ir)
                            return constants.state_var

                        self.find_definition(rht_val0, dep_set, ir_list)
                        self.find_definition(rht_val1, dep_set, ir_list)

                    else:
                        if constants.ffff in ir_rht_val or '0x' in ir_rht_val:
                            return
                        rht_val = ir_rht_val.split('(')[1].split(')')[0].strip()

                        self.find_definition(rht_val, dep_set, ir_list)
                        if constants.timestamp in ir_rht_val:
                            # print('find timestamp')
                            dep_set.add(constants.timestamp)
                            ir_list.append(ir)
                            return constants.timestamp

                        if constants.calldataload in ir_rht_val:
                            # print('find call data load')
                            ir_list.append(ir)
                            dep_set.add(constants.user_input)
                            return constants.user_input

                        # special case of balance
                        if constants.balance in ir_rht_val:
                            ir_list.append(ir)
                            dep_set.add(constants.balance)

                        if constants.caller in ir_rht_val:
                            ir_list.append(ir)
                            dep_set.add(constants.user)


                        if constants.sload in ir_rht_val:
                            # print('find sload')
                            ir_list.append(ir)
                            dep_set.add(constants.state_var)
                            return constants.state_var

    def get_mstore_value(self, mstore_ir):
        # print('mstore ir ', mstore_ir)
        if '[NO_SSA]' in mstore_ir:
            return
        val = mstore_ir.split('MSTORE(')[1].split(',')[1].split(')')[0].strip()
        return val

    def find_next_n_mstore(self, ir, n):
        mstore_cnt = 0
        mstore_ir_list = []
        ir_idx = self.ir_list.index(ir)
        for i in range(ir_idx, len(self.ir_list)):
            if constants.mstore in self.ir_list[i]:
                mstore_cnt += 1
                mstore_ir_list.append(self.ir_list[i])

            if mstore_cnt == n:
                break

        return mstore_ir_list[1:]

    def get_ir_list(self):
        print('fname ', self.fname)
        graph = pydot.graph_from_dot_file(self.fname)[0]
        # print(graph)
        bb_ir_list = str(graph).split('subgraph global {')[1].split('}')[0].split('\n')
        # print(bb_ir_list)
        ir_list = []

        for bb_ir in bb_ir_list:
            if bb_ir == '' or 'fontname=Courier, fontsize' in bb_ir:
                continue
            format_ir_list = bb_ir.split('"')[1].split('"')[0].split('\l')
            format_ir_list = [ir.split(':')[1].strip() for ir in format_ir_list if ir != '']
            ir_list += format_ir_list

        return ir_list, bb_ir_list


STATIC_ANALYSIS_CMD = 'python3 octopus_eth_evm.py -s -f '
NLG_CMD = 'python3 ctfg_analysis.py'


def main():
    import csv

    with open('node.csv', 'w') as f:
        csvwriter = csv.writer(f)
        n_list = []
        for i in range(600):
            il = [i]
            csvwriter.writerow(il)



if __name__ == "__main__":
    main()
