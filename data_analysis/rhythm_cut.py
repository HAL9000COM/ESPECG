# %%
import pandas as pd
import numpy as np


# %%
def rhythm_anno(anno: pd.DataFrame, sample: int):
    """
    get rhythm anno from anno
    input: anno, sample
    output: rhythm anno, rhythm sample
    """
    i = 0
    while (
        anno["Sample #"][i] < sample
        and anno["Sample #"][i + 1] < sample
        and i < len(anno) - 2
    ):
        i += 1
    # i: lastest anno before sample
    n = 0
    while anno["Aux"][i - n] is np.nan:
        n += 1
    # i-n: lastest rhythm anno before sample
    return anno["Aux"][i - n], anno["Sample #"][i - n]


def segment_10s(data: pd.DataFrame, anno: pd.DataFrame, sample_rate: int = 360):
    """
    segment 10s data from data and get anno
    """
    samples = 10 * sample_rate
    data_list = []
    anno_list = []
    for i in range(0, len(data), samples):
        data_list.append(data[i : i + samples])
        anno_item, rhythm_sample = rhythm_anno(
            anno, i + samples
        )  # too many indexing search
        anno_list.append(anno_item)
    return data_list, anno_list


# %%
path = "mit-bih-arrhythmia-database-1.0.0/x_mitdb"
import os

save_path = "data"
save_path = os.path.join(path, save_path)
if os.path.exists(save_path) is False:
    os.mkdir(save_path)

f = open(os.path.join(path, "RECORDS"), "r")
# read file
lines = f.readlines()
# remove \n
lines = [line.strip() for line in lines]

# %%

for line in lines:
    name = str(line)
    data_path = os.path.join(path, name + ".txt")
    anno_path = os.path.join(path, name + "_at.txt")
    data = pd.read_csv(data_path, sep="\t")
    data.columns = [column.strip() for column in data.columns]
    if "MLII" in data.columns:
        pass
    else:
        continue
    anno = pd.read_fwf(anno_path, widths=[12, 9, 6, 5, 5, 5, 4])
    data_list, anno_list = segment_10s(data, anno)
    for i in range(len(data_list)):
        anno_list[i] = anno_list[i].replace("(", "")
        sub_dir = os.path.join(save_path, anno_list[i])
        if os.path.exists(sub_dir) is False:
            os.mkdir(sub_dir)
        csv_path = oscsv_path = os.path.join(sub_dir, name + "_" + str(i) + ".csv")
        data_list[i]["MLII"].to_csv(csv_path, index=False)
        print(csv_path)
