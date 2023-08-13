# %%
import pandas as pd
import numpy as np


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
def segment_beat(data, anno, sample_rate=360, f1=0.5, f2=0.5):
    """
    segment beat data with beat in in the center
    input: data, anno, sample_rate, f1, f2
    output: data_list, anno_list
    """
    f1 = int(f1 * sample_rate)
    f2 = int(f2 * sample_rate)
    data_list = []
    anno_list = []
    for i in range(len(anno)):
        data_list.append(
            data[
                max(0, anno["Sample #"][i] - f1) : min(
                    len(data) - 1, anno["Sample #"][i] + f2
                )
            ]
        )
        anno_list.append(anno["Type"][i])
    return data_list, anno_list


# %%
path = "mit-bih-arrhythmia-database-1.0.0/x_mitdb"
import os

save_path = "beat_data"
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
    data_list, anno_list = segment_beat(data, anno)
    for i in range(len(data_list)):
        anno_list[i] = anno_list[i].strip()
        anno_list[i] = translate_annotation(anno_list[i])
        sub_dir = os.path.join(save_path, anno_list[i])
        if os.path.exists(sub_dir) is False:
            os.mkdir(sub_dir)
        csv_path = oscsv_path = os.path.join(sub_dir, name + "_" + str(i) + ".csv")
        data_list[i]["MLII"].to_csv(csv_path, index=False)
        print(csv_path)

# %%
# %%
