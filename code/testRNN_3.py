import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.models import load_model, Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

# Cargar y preprocesar el archivo de datos
data = pd.read_csv('historical/history_positions_4.csv')

# Normalizar los datos
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['latitude', 'longitude']])

# Crear ventanas de tiempo para la predicción
def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - time_step - 1):
        a = dataset[i:(i + time_step), :]
        dataX.append(a)
        dataY.append(dataset[i + time_step, :])
    return np.array(dataX), np.array(dataY)

time_step = 100
X, y = create_dataset(scaled_data, time_step)

# Dividir los datos en conjuntos de entrenamiento y prueba
train_size = int(len(X) * 0.8)
test_size = len(X) - train_size
X_train, X_test = X[0:train_size], X[train_size:len(X)]
y_train, y_test = y[0:train_size], y[train_size:len(y)]

# Definir y entrenar el modelo RNN LSTM
model = Sequential()
model.add(LSTM(300, return_sequences=True, input_shape=(time_step, 2)))
model.add(Dropout(0.3))
model.add(LSTM(300, return_sequences=True))
model.add(Dropout(0.3))
model.add(LSTM(300, return_sequences=False))
model.add(Dropout(0.3))
model.add(Dense(150))
model.add(Dense(2))

model.compile(optimizer='adam', loss='mean_squared_error')

# Guardar el mejor modelo durante el entrenamiento
checkpoint = ModelCheckpoint('best_model.keras', monitor='val_loss', save_best_only=True, mode='min')

# Entrenar el modelo
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=300, batch_size=64, verbose=1, callbacks=[checkpoint])

# 3. Predicción y validación
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# Invertir la normalización
train_predict = scaler.inverse_transform(train_predict)
y_train = scaler.inverse_transform(y_train)
test_predict = scaler.inverse_transform(test_predict)
y_test = scaler.inverse_transform(y_test)

# Validar las predicciones
def validate_predictions(predictions):
    validated = []
    for pred in predictions:
        if -90 <= pred[0] <= 90 and -180 <= pred[1] <= 180:
            validated.append(pred)
    return np.array(validated)

validated_train_predict = validate_predictions(train_predict)
validated_test_predict = validate_predictions(test_predict)

# 4. Exportación del modelo
model.save('model_RNN_3.keras')

# 5. Plotting de los resultados
plt.figure(figsize=(14, 7))

# Plotear los datos históricos
plt.plot(data['latitude'], label='Latitud histórica')
plt.plot(data['longitude'], label='Longitud histórica')

# Plotear las predicciones
plt.plot(range(time_step, time_step + len(validated_train_predict)), validated_train_predict[:, 0], label='Predicción de latitud (entrenamiento)')
plt.plot(range(len(data) - len(validated_test_predict), len(data)), validated_test_predict[:, 0], label='Predicción de latitud (prueba)')
plt.plot(range(time_step, time_step + len(validated_train_predict)), validated_train_predict[:, 1], label='Predicción de longitud (entrenamiento)')
plt.plot(range(len(data) - len(validated_test_predict), len(data)), validated_test_predict[:, 1], label='Predicción de longitud (prueba)')

plt.xlabel('Tiempo')
plt.ylabel('Posición')
plt.legend()
plt.show()
