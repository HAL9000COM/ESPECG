# %%
import tensorflow as tf
import numpy as np
import pandas as pd
import os

# %%
# Define the path to the parent directory containing the CSV files
parent_dir = "mit-bih-arrhythmia-database-1.0.0/data"

# get the list of all the CSV files in the parent directory
dir_list = os.listdir(parent_dir)
# %%
data = []
for dir in dir_list:
    data_array = []
    file_list = os.listdir(os.path.join(parent_dir, dir))
    for file in file_list:
        if file.endswith(".csv"):
            # Read the CSV file into a Pandas data frame
            df = pd.read_csv(os.path.join(parent_dir, dir, file))
            # Convert the Pandas data frame to a NumPy array
            csv_data = df.to_numpy()
            csv_data = np.squeeze(csv_data)

            # Append the NumPy array to the Python list
            data_array.append(csv_data)
    data_array = tf.keras.utils.pad_sequences(
        data_array,
        maxlen=3600,
        dtype="int32",
        padding="post",
        truncating="post",
        value=0,
    )
    label = [str(dir) for i in range(data_array.shape[0])]
    print(data_array.shape)
    data.append(tf.data.Dataset.from_tensor_slices((data_array, label)))
    print(dir + " done")


for i in range(1, len(data)):
    data[0] = data[0].concatenate(data[i])
data = data[0]

label_list = dir_list


def label_to_int(x, label):
    label_number = tf.argmax(tf.cast(tf.equal(label_list, label), tf.int32))
    return x, tf.cast(label_number, dtype=tf.int32)


data = data.map(label_to_int)
# %%
tf_data_save_path = os.path.join(os.path.dirname(parent_dir), "tf_data")
data.save(tf_data_save_path)

with open(os.path.join(tf_data_save_path, "label_list.txt"), "w") as f:
    f.write(str(label_list))
# %%
