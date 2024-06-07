# %%
import os

import numpy as np
import tensorflow as tf

# %%
data_path = "tf_data/beat_data"
# load npz
arrays = np.load(os.path.join(data_path, "data.npz"))
data = arrays["data"]
label = arrays["label"]
# convert label to one-hot
label = tf.keras.utils.to_categorical(label, num_classes=17)
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
batch_size = 128

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
dataset = dataset.cache().batch(batch_size).prefetch(buffer_size=tf.data.AUTOTUNE)
# %%
# Define the model
model = tf.keras.Sequential(
    [
        tf.keras.layers.InputLayer(input_shape=(360,)),
        tf.keras.layers.Dense(units=128, activation=tf.keras.layers.PReLU()),
        tf.keras.layers.Dense(units=64, activation=tf.keras.layers.PReLU()),
        tf.keras.layers.Dense(units=17, activation="softmax"),
    ]
)

# Compile the model
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    # loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    loss=tf.keras.losses.CategoricalCrossentropy(),
    metrics=["accuracy"],
)

# Print the model summary
model.summary()
# %%
# Define the callbacks
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=20, restore_best_weights=True
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.1, patience=5, verbose=1
    ),
]


# %%
# Train the model
model.fit(data_train, epochs=100, validation_data=data_test, callbacks=callbacks)

# %%
# Save the model
model.save("model.h5")

# %%
# draw confusion matrix with percentage
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix

# get confusion matrix
y_pred = model.predict(data_train)
y_pred = np.argmax(y_pred, axis=1)
y_true = np.concatenate([y for x, y in data_train], axis=0)
y_true = np.argmax(y_true, axis=1)
cm = confusion_matrix(y_true, y_pred)
cm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
# draw confusion matrix
plt.figure(figsize=(10, 10))
sns.heatmap(cm, annot=True, fmt=".2f", cmap="Blues", square=True)
plt.ylabel("Actual label")
plt.xlabel("Predicted label")
plt.xticks(np.arange(17) + 0.5, label_list, rotation=90)
plt.yticks(np.arange(17) + 0.5, label_list, rotation=0)
plt.title("Confusion matrix")
plt.show()
# %%
from everywhereml.code_generators.tensorflow import convert_model

# %%
cpp_code = convert_model(model, data, label, model_name="ecgmodel")
# %%
with open("../esp32/ecgmodel.h", "w") as f:
    f.write(cpp_code)
# %%
