# %%
import pandas as pd
import numpy as np
import os
from ray.util.multiprocessing import Pool


def translate_annotation(annotation):
    match annotation:
        case "·" | "N":
            return "Normal beat"
        case "L":
            return "Left bundle branch block beat"
        case "R":
            return "Right bundle branch block beat"
        case "A":
            return "Atrial premature beat"
        case "a":
            return "Aberrated atrial premature beat"
        case "J":
            return "Nodal premature beat"
        case "S":
            return "Supraventricular premature beat"
        case "V":
            return "Premature ventricular contraction"
        case "F":
            return "Fusion of ventricular and normal beat"
        case "[":
            return "Start of ventricular fibrillation"
        case "!":
            return "Ventricular flutter wave"
        case "]":
            return "End of ventricular fibrillation"
        case "e":
            return "Atrial escape beat"
        case "j":
            return "Nodal escape beat"
        case "E":
            return "Ventricular escape beat"
        case "/":
            return "Paced beat"
        case "f":
            return "Fusion of paced and normal beat"
        case "x":
            return "Non-conducted P-wave (blocked APB)"
        case "Q":
            return "Unclassifiable beat"
        case "|":
            return "Isolated QRS-like artifact"
        case _:
            return "Unknown beat type"


# %%
def segment_beat(data, anno, sample_rate=360, t1=0.25, t2=0.45):
    """
    segment beat data with beat in in the center
    input: data, anno, sample_rate, t1, t2
    output: data_list, anno_list
    """
    t1 = int(t1 * sample_rate)
    t2 = int(t2 * sample_rate)
    data_list = []
    anno_list = []
    for i in range(len(anno)):
        data_list.append(
            data[
                max(0, anno["Sample #"][i] - t1) : min(
                    len(data) - 1, anno["Sample #"][i] + t2
                )
            ]
        )
        anno_list.append(anno["Type"][i])
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
    data_list, anno_list = segment_beat(data, anno, sample_rate)
    for i in range(len(data_list)):
        anno_list[i] = anno_list[i].strip()
        anno_list[i] = translate_annotation(anno_list[i])
        sub_dir = os.path.join(save_path, anno_list[i])
        if os.path.exists(sub_dir) is False:
            os.mkdir(sub_dir)
        csv_path = os.path.join(sub_dir, name + "_" + str(i) + ".csv")
        data_list[i][data_label].to_csv(csv_path, index=False)
        print(csv_path)


# %%

colums_width_dict = {"mit-bih-arrhythmia": [12, 9, 6, 5, 5, 5, 4]}

path = "datasets/mit-bih-arrhythmia-database-1.0.0/x_mitdb"
save_path = "beat_data"

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
# %%
