import os
import glob

STATIC_ANALYSIS_CMD = 'python3 octopus_eth_evm.py -s -f '
NLG_CMD = 'python3 flow_analysis.py'

bin_files = glob.glob("eth-binary-contracts/2/*")
for bin in bin_files:
    analysis_cmd = STATIC_ANALYSIS_CMD + bin
    os.system(analysis_cmd)

os.system(NLG_CMD)

# print(glob.glob("graph/*"))