from slither.printers.abstract_printer import AbstractPrinter
API_LIST = ['transferFrom']


class TransferVarDict:
    def __init__(self, statement, transfer_id, param_id):
        self.statement = statement
        self.transfer_id = transfer_id
        self.param_id = param_id

    def __str__(self) -> str:
        return 's' + str(self.transfer_id) + 'p' + self.param_id   

class Sol2Graph(AbstractPrinter):

    ARGUMENT = "sol2graph"
    HELP = "Export the CTFG of each functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#cfg"

    def output(self, filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        info = ""
        all_files = []
        for contract in self.contracts:
            transfer_id = 0

            if contract.is_top_level:
                continue
            for function in contract.functions + contract.modifiers:
                for node in function.nodes:
                    for api in API_LIST:
                        if api in str(node):
                            if filename:
                                new_filename = "{}-{}-{}.dot".format(
                                    filename, contract.name, function.full_name
                                )
                            else:
                                # if is amount, set 2
                                trt = TransferVarDict(transfer_id, 2, 2)
                                new_filename = "{}-{}.dot".format(contract.name, function.full_name)
                            info += "Export {}\n".format(new_filename)
                            content = function.slithir_cfg_to_dot_str()
                            with open(new_filename, "w", encoding="utf8") as f:
                                f.write(content)
                            all_files.append((new_filename, content))

        self.info(info)

        res = self.generate_output(info)
        for filename_result, content in all_files:
            res.add_file(filename_result, content)
        return res
    
    def slithir_cfg_to_dot_str(self, skip_expressions=False) -> str:
        """
        Export the CTFG to a DOT format. The nodes includes the Solidity expressions and the IRs
        :return: the DOT content
        :rtype: str
        """
        from slither.core.cfg.node import NodeType

        content = ""
        content += "digraph{\n"
        for node in self.nodes:
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