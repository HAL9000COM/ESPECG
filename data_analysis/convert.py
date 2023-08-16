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
new_data_path = os.path.join(folder, "txt_data")
if os.path.exists(new_data_path) is False:
    os.mkdir(new_data_path)
for line in lines:
    path = folder + line
    save_path = new_data_path + "/" + line
    os.system("wfdbdesc " + path + " >" + save_path + "_info.txt")
    os.system("rdann -r " + path + " -a atr -v >" + save_path + "_atr.txt")
    os.system("rdsamp -r " + path + " -v >" + save_path + ".txt")
    os.system("rdsamp -r " + path + " -p -v >" + save_path + "_real.txt")
    print(line + " done")
