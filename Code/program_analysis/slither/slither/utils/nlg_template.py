from operator import mod, rshift
import simplenlg
from simplenlg.framework import *
from simplenlg.lexicon import *
from simplenlg.realiser.english import *
from simplenlg.phrasespec import *
from simplenlg.features import *

SOLIDITY_VAR_DICT = {'msg.value': 'the given fund'}
IF = 'If'
NOT = 'not'

class Modifier:
    def __init__(self, sub, pred, obj):
        self.sub = sub
        self.pred = pred
        self.obj = obj

    def to_sen(self):
        lexicon = Lexicon.getDefaultLexicon()
        nlgFactory = NLGFactory(lexicon)
        realiser = Realiser(lexicon)
        statement_spec = nlgFactory.createClause(self.sub, self.pred, self.obj)
        return realiser.realiseSentence(statement_spec)


class Statement:
    def __init__(self, sub, pred, obj):
        self.sub = sub
        self.pred = pred
        self.obj = obj

    def get_description(self):
        lexicon = Lexicon.getDefaultLexicon()
        nlgFactory = NLGFactory(lexicon)
        realiser = Realiser(lexicon)
        statement_spec = nlgFactory.createClause(self.sub, self.pred, self.obj)
        return realiser.realiseSentence(statement_spec)


class SimplenlgGenerator:
    
    def __init__(self) -> None:
        pass

    def generate_condition_res_sen(self, modifier_list, conj_list, statement):  
        return self.generate_modifier_list(modifier_list, conj_list) + self.generate_res_sen(statement)

    def generate_res_sen(self, statement: Statement):
        res = statement.get_description()      
        return res[0].lower() + res[1:]
    
    # generate multiple [if node] + [res node] sentence
    def generate_multiple_modifier_list(self, mul_modifer_list, mul_conj_list, statement: Statement):
        if len(mul_modifer_list) == 0:
            return ''
        if len(mul_modifer_list) == 1:
            return self.generate_condition_res_sen(mul_modifer_list[0], mul_conj_list[0], statement)

        res = ''
        for i in range(len(mul_modifer_list)):
            mlsen = self.generate_modifier_list(mul_modifer_list[i], mul_conj_list[i])
            if i == 0:
                modifier_sen = mlsen
            else:
                modifier_sen = 'and ' + mlsen[0].lower() + mlsen[1:]
            res += modifier_sen

        res += self.generate_res_sen(statement)
        return res

    # generate one condition sentence with multiple and/or
    def generate_modifier_list(self, modifier_list, conj_list):
        lexicon = Lexicon.getDefaultLexicon()
        nlgFactory = NLGFactory(lexicon)
        realiser = Realiser(lexicon)

        modifier_sen = 'If '

        if len(modifier_list) == 1:
            modifier = modifier_list[0]
            spharse_spec = nlgFactory.createClause(modifier.sub, modifier.pred, modifier.obj)
            output = realiser.realiseSentence(spharse_spec)
            return  (modifier_sen + output[0].lower() + output[1:])[0:-1] + ', '

        for i in range(len(modifier_list)):
            modifier = modifier_list[i]
            spharse_spec = nlgFactory.createClause(modifier.sub, modifier.pred, modifier.obj)
            output = realiser.realiseSentence(spharse_spec)

            if i != len(modifier_list) - 1:
                modifier_sen += output[0].lower() + output[1:].replace('.', ',') + ' ' + conj_list[i] + ' '
            else:
                modifier_sen += output
            
        return modifier_sen[0: -1] + ', '
   
m0 = Modifier('the contract', 'send', 'user specified state variable')
m1 = Modifier('usas', 'be greater than', 'state variable')
m2 = Modifier('local variable', 'be', '1')


# modifier_list = [m0, m1, m2]
m0 = Modifier('the amount of ether sent', 'equal to', '10 ether')
m1 = Modifier('timestamp modula 15', 'be', 'zero')

sg = SimplenlgGenerator()



# mul_m_list = [[m0], [m1]]
# res = sg.generate_multiple_modifier_list(mul_m_list, [['and']], s)
# print(res)
sg = SimplenlgGenerator()
# print(sg.generate_modifier_list(modifier_list, ['and', 'or', 'and']))               
mul_m_list = [[m0, m1]]
con_list = [['and']]
s = Statement('the contract', 'transfer', 'the balance of the contract')
# print(sg.generate_multiple_modifier_list(mul_m_list, con_list, s))


# s0 = Statement('the amount swapped in, the amount swapped out and paid fee', 'be', 'the computed result of a swap within ticks')
# s1 = Statement('the remaining amount to be swapped', 'be', 'decresed by the amount swapped in plus paid fee at this step')

# print(s0.get_description())
# print(s1.get_description())

lexicon = Lexicon.getDefaultLexicon()
nlgFactory = NLGFactory(lexicon)
realiser = Realiser(lexicon)
s0 = nlgFactory.createClause('The amount', 'be', 'user input value')
s1 = nlgFactory.createClause('The amount', 'be', 'calculated value depending on user specified input value and specific date value')
c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s0)
c.addCoordinate(s1)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)
s01 = nlgFactory.createClause('The contract', 'transfer', 'amount from the user input address to another user input address')
# s1 = nlgFactory.createClause('The contract', 'transfer', 'calculated value of user specified input value and specific date value from the user input address to user input address')

c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s01)
# c.addCoordinate(s1)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)

s2 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value to another user input address')
s3 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value from another user input address to another user input address')

c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s2)
c.addCoordinate(s3)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)

s4 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value to another user input address')
s5 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value from user input address to another user input address')

c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s4)
c.addCoordinate(s5)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)

s6 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value to third party address')
s7 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value from another user input address to third party address')

c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s6)
c.addCoordinate(s7)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)

s8 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value to third party address')
s9 = nlgFactory.createClause('The contract', 'transfer', 'calculated value depending on transferred amount and user input value from user input address to third party address')

c = nlgFactory.createCoordinatedPhrase()
c.addCoordinate(s6)
c.addCoordinate(s7)
c.setConjunction('or')
output = realiser.realiseSentence(c)
print(output)
# s0_sen = nlgFactory.createSentence(s0)
# s1_sen = nlgFactory.createSentence(s1)
# print(s0_sen)

# sen_list = [s0_sen, s1_sen]
# realiser = Realiser(lexicon)
# p = nlgFactory.createParagraph(sen_list)
# output = realiser.realise(p).getRealisation()

# print(output)