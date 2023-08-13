# coding=utf-8
import sys
import os

# %%
folder = sys.argv[1] + "/"
f = open(folder + "RECORDS", "r")
# read file
lines = f.readlines()
# remove \n
lines = [line.strip() for line in lines]

# %%

for line in lines:
    path = folder + line
    os.system("wfdbdesc " + path + " >" + path + "_info.txt")
    os.system("rdann -r " + path + " -a atr -v >" + path + "_at.txt")
    os.system("rdsamp -r " + path + " -v >" + path + ".txt")
    os.system("rdsamp -r " + path + " -p -v >" + path + "_real.txt")
    print(line + " done")
