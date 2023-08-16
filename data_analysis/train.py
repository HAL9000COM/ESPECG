# %%
import tensorflow as tf
import os
import numpy as np

# %%
data_path = "tf_data/beat_data"
# load npz
arrays = np.load(os.path.join(data_path, "data.npz"))
data = arrays["data"]
label = arrays["label"]
# get array from npz
dataset = tf.data.Dataset.from_tensor_slices((data, label))
with open(os.path.join(data_path, "label_list.txt"), "r") as f:
    label_list = f.read()
label_list = eval(label_list)
dataset_size = dataset.reduce(0, lambda x, _: x + 1)

# Print the size of the dataset
print(f"The x shape of the dataset is {dataset.element_spec[0].shape}.")
print(f"The y shape of the dataset is {dataset.element_spec[1].shape}.")
print(f"The size of the dataset is {dataset_size}.")
print(f"The labels in the dataset are {label_list}.")
print(f"The number of labels is {len(label_list)}.")
# %%
split_ratio = 0.8
batch_size = 32

# shuffle the data
data_train, data_test = tf.keras.utils.split_dataset(
    dataset, left_size=split_ratio, shuffle=True
)
data_train = (
    data_train.cache()
    .shuffle(buffer_size=int(dataset_size), reshuffle_each_iteration=True)
    .batch(batch_size)
    .prefetch(buffer_size=tf.data.AUTOTUNE)
)
data_test = data_test.cache().batch(batch_size).prefetch(buffer_size=tf.data.AUTOTUNE)

# %%
# Define the model
model = tf.keras.Sequential(
    [
        tf.keras.layers.InputLayer(input_shape=(3600,)),
        tf.keras.layers.Reshape(target_shape=(3600, 1)),
        tf.keras.layers.Conv1D(filters=32, kernel_size=5, strides=2, activation="relu"),
        tf.keras.layers.MaxPooling1D(pool_size=2, strides=2),
        tf.keras.layers.Conv1D(filters=64, kernel_size=5, strides=2, activation="relu"),
        tf.keras.layers.MaxPooling1D(pool_size=2, strides=2),
        tf.keras.layers.Conv1D(
            filters=128, kernel_size=5, strides=2, activation="relu"
        ),
        tf.keras.layers.MaxPooling1D(pool_size=2, strides=2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(16, activation="softmax"),
    ]
)

# Compile the model
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=["accuracy"],
)

# Print the model summary
model.summary()

# %%
# Train the model
model.fit(data_train, epochs=10, validation_data=data_test)

# %%
