# %%
import numpy as np
import os
import tensorflow as tf
from ray.util.multiprocessing import Pool

# %%
# Define the path to the parent directory containing the CSV files
DATA_TYPE = "rhythm"
SAMPLE_LENGTH = 3600

parent_dir = "mit-bih-arrhythmia-database-1.0.0"
tf_data_save_path = "tf_data"

if DATA_TYPE == "beat":
    parent_dir = os.path.join(parent_dir, "beat_data")
    tf_data_save_path = os.path.join(tf_data_save_path, "beat_data")
elif DATA_TYPE == "rhythm":
    parent_dir = os.path.join(parent_dir, "rhythm_data")
    tf_data_save_path = os.path.join(tf_data_save_path, "rhythm_data")
# get the list of all the CSV files in the parent directory
dir_list = os.listdir(parent_dir)


# %%
def read_csv(file):
    csv_data = np.loadtxt(file, delimiter=",", skiprows=1)
    csv_data = np.squeeze(csv_data)
    return csv_data


# %%
data_list = []
label_list = []
p = Pool()
for dir in dir_list:
    file_list = os.listdir(os.path.join(parent_dir, dir))
    file_paths = [
        os.path.join(parent_dir, dir, file)
        for file in file_list
        if file.endswith(".csv")
    ]
    csv_data_list = p.map(read_csv, file_paths)
    for csv_data in csv_data_list:
        # Append the NumPy array to the Python list
        data_list.append(csv_data)
        label_list.append(dir_list.index(dir))
    print(dir + " done")
p.close()

# %%
data = tf.keras.utils.pad_sequences(
    data_list,
    maxlen=SAMPLE_LENGTH,
    dtype="int32",
    padding="post",
    truncating="post",
    value=0,
)
label = np.array(label_list)
# %%
print(data.shape)
print(label.shape)
# %%
# save as npz

if not os.path.exists(tf_data_save_path):
    os.makedirs(tf_data_save_path)
np.savez_compressed(os.path.join(tf_data_save_path, "data.npz"), data=data, label=label)

with open(os.path.join(tf_data_save_path, "label_list.txt"), "w") as f:
    f.write(str(dir_list))
# %%
