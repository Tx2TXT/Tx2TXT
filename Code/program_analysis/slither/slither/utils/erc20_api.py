class ERC20_API:
    def __init__(self, func_name, arg_list):
        self.func_name = str(func_name)
        self.arg_list = arg_list

    def get_description(self):
        print('self func name ', self.func_name)
        func_name = self.func_name
        if func_name == 'totalSupply':
            return self.erc20_totalSupply()
        if func_name == 'balanceOf':
            return self.erc20_balanceOf()
        if func_name == 'allowance':
            return self.erc20_allowance()        
        if func_name == 'transfer':
            return self.erc20_transfer()
        if func_name == 'approve':
            return self.erc20_approve()
        if func_name == 'transferFrom':
            return self.erc20_transferFrom()        
        
        return ''

    def erc20_totalSupply(self):
        return 'the amount of tokens in existence is %s' % (self.arg_list[0])

    def erc20_balanceOf(self):
        return 'the amount of tokens owned is %s' % (self.arg_list[0])

    def erc20_allowance(self):
        return 'the remaining number of tokens that %s will be allowed to spend on behalf of %s through transferFrom.' % (self.arg_list[1], self.arg_list[0])

    def erc20_transfer(self):
        return 'moves %s tokens from the caller\'s account to %s' % (self.arg_list[1], self.arg_list[0])

    def erc20_approve(self):
        return 'sets %s as the allowance of %s over the caller\'s tokens.' % (self.arg_list[1], self.arg_list[0])

    def erc20_transferFrom(self):
        return 'moves %s tokens from %s to %s using the allowance mechanism. %s is then deducted from the caller\'s allowance.' % (self.arg_list[2], self.arg_list[0], self.arg_list[1], self.arg_list[2])
