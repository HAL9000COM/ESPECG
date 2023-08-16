# %%
import pandas as pd
import numpy as np
import os
from ray.util.multiprocessing import Pool


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


def process_data(in_data: list):
    line, path, save_path, colums_width, data_label, sample_rate = in_data
    name = str(line)
    data_path = os.path.join(path, name + ".txt")
    anno_path = os.path.join(path, name + "_atr.txt")
    data = pd.read_csv(data_path, sep="\t")
    data.columns = [column.strip() for column in data.columns]
    if data_label in data.columns:
        pass
    else:
        return
    anno = pd.read_fwf(anno_path, widths=colums_width)
    data_list, anno_list = segment_10s(data, anno, sample_rate)
    for i in range(len(data_list)):
        anno_list[i] = anno_list[i].replace("(", "")
        sub_dir = os.path.join(save_path, anno_list[i])
        if os.path.exists(sub_dir) is False:
            os.mkdir(sub_dir)
        csv_path = os.path.join(sub_dir, name + "_" + str(i) + ".csv")
        data_list[i][data_label].to_csv(csv_path, index=False)
        print(csv_path)


# %%
colums_width_dict = {"mit-bih-arrhythmia": [12, 9, 6, 5, 5, 5, 4]}

path = "datasets/mit-bih-arrhythmia-database-1.0.0/x_mitdb"
save_path = "rhythm_data"

DATA_TYPE = "mit-bih-arrhythmia"
SAMPLE_RATE = 360
DATA_LABEL = "MLII"

save_path = os.path.join(path, save_path)
if os.path.exists(save_path) is False:
    os.mkdir(save_path)


f = open(os.path.join(path, "RECORDS"), "r")
# read file
lines = f.readlines()
# remove \n
lines = [line.strip() for line in lines]

# %%
in_data = [
    (
        line,
        path + "/txt_data",
        save_path,
        colums_width_dict[DATA_TYPE],
        DATA_LABEL,
        SAMPLE_RATE,
    )
    for line in lines
]
p = Pool()
p.map(process_data, in_data)
p.close()
# %%
