class TransferVarDict:
    def __init__(self, statement, transfer_id, param_id):
        self.statement = statement
        self.transfer_id = transfer_id
        self.param_id = param_id

    def __str__(self) -> str:
        return 's' + str(self.transfer_id) + 'p' + self.param_id   