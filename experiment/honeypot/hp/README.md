The dir contains honeypot cases from HoneyBadger(https://github.com/christoftorres/HoneyBadger)

We evaluated 28 general cases(https://github.com/christoftorres/HoneyBadger/tree/master/datasets/honeypots) and datasets of 282 contracts(https://github.com/christoftorres/HoneyBadger/tree/master/results/evaluation).

Tx2TXT can cover 10/28 = **35.7%** general cases and total 166/282 = **58.9%** contracts in the dataset.



Tx2TXT can handle cases with malicious conditions like 

- Hidden transfer: The contract tries to hide a transfer from the user account to an unknown account and misleads the user to believe it is a single transfer function. (TestToken.sol)

- Compare a user input value with a **timestamp hash** (CryptoRoulette.sol)
- Unreachable condition using balance e.g. `msg.value>=this.balance` is **unreachable** because `address(this).balance >= msg.value` is always true (MultiplicatorX3.sol)



Those cases that Tx2TXT cannot cover are 

- syntax(compiler) problems (TestBank.sol) 
- endless calculation in a loop (RACEFORETH.sol)



We focus on business logic instead of some basic syntax problems. Meanwhile, the calculation can be very complex and tricky to solve. As a result, Tx2TXT cannot cover these two kinds of honeypot cases.

