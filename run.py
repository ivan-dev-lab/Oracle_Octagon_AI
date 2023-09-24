from sklearn.model_selection import train_test_split
from AI.preprocess import preprocess
from AI.model import create_model, callbacks

X,Y = preprocess(fp_fighters="data/fighters.csv", fp_fights="data/fights.csv")
x_train, x_test, y_train, y_test = train_test_split(X,Y, test_size=0.2, random_state=42)

model = create_model(X.shape[1])
model.fit(x_train,
          y_train, 
          batch_size=32, 
          epochs=20, 
          validation_data=(x_test, y_test),
          verbose=0,
          callbacks=callbacks(),
          )


model.load_weights("model/weights.h5")
score = model.evaluate(x_test, y_test)

print(f"Точность модели на тестовых данных: {round(score[1],2)*100}%")