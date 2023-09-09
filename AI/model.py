from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import Model, layers
from keras.models import Sequential
from keras.optimizers import Adam

def callbacks () -> list:
    early_stopping = EarlyStopping(monitor="val_accuracy", min_delta=0.01, patience=7, restore_best_weights=True)
    model_checkpoint = ModelCheckpoint(filepath="model/", monitor="val_accuracy", save_best_only=True, save_weights_only=True)

    return [early_stopping, model_checkpoint]

def create_model (input_shape: int) -> Model:
    model = Sequential()
    model.add(layers.Dense(units=256, activation="tanh", input_shape=(input_shape,)))
    model.add(layers.Dropout(0.4))
    model.add(layers.Dense(units=128, activation="relu"))
    model.add(layers.Dropout(0.3))
    model.add(layers.Dense(units=64, activation="tanh"))
    model.add(layers.Dense(units=32, activation="relu"))
    model.add(layers.Dense(units=2, activation="softmax"))

    model.compile(optimizer=Adam(learning_rate=0.0001), loss="categorical_crossentropy", metrics=["accuracy"])
    return model