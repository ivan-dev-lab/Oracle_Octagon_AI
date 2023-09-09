import tensorflow as tf
from keras import Model, layers
from keras.models import Sequential
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
from preprocess import preprocess

early_stopping = EarlyStopping(monitor="val_accuracy", min_delta=0.01, patience=7, restore_best_weights=True)
model_checkpoint = ModelCheckpoint(filepath="model/", monitor="val_accuracy", save_best_only=True, save_weights_only=True)

callbacks = [early_stopping, model_checkpoint]

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

X,Y = preprocess(fp_fighters="data/fighters.csv", fp_fights="data/fights.csv")
x_train, x_test, y_train, y_test = train_test_split(X,Y, test_size=0.2, random_state=42)

model = create_model(X.shape[1])
model.fit(x_train,
          y_train, 
          batch_size=32, 
          epochs=20, 
          validation_data=(x_test, y_test),
          # callbacks=callbacks,
          )


model.load_weights("model/")
score = model.evaluate(x_test, y_test)
print(score[1]) # 0.72