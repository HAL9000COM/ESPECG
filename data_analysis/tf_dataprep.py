# %%
import numpy as np
import pandas as pd
import os
import tensorflow as tf

# %%
# Define the path to the parent directory containing the CSV files
parent_dir = "mit-bih-arrhythmia-database-1.0.0/data"

# get the list of all the CSV files in the parent directory
dir_list = os.listdir(parent_dir)
# %%
data_list = []
label_list = []
for dir in dir_list:
    file_list = os.listdir(os.path.join(parent_dir, dir))
    for file in file_list:
        if file.endswith(".csv"):
            # Read the CSV file into a Pandas data frame
            df = pd.read_csv(os.path.join(parent_dir, dir, file))
            # Convert the Pandas data frame to a NumPy array
            csv_data = df.to_numpy()
            csv_data = np.squeeze(csv_data)

            # Append the NumPy array to the Python list
            data_list.append(csv_data)
            label_list.append(dir_list.index(dir))
    print(dir + " done")

# %%
data = tf.keras.utils.pad_sequences(
    data_list,
    maxlen=3600,
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
tf_data_save_path = "tf_data"
if not os.path.exists(tf_data_save_path):
    os.makedirs(tf_data_save_path)
np.savez_compressed(os.path.join(tf_data_save_path, "data.npz"), data=data, label=label)

with open(os.path.join(tf_data_save_path, "label_list.txt"), "w") as f:
    f.write(str(dir_list))
# %%
