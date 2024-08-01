import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.callbacks import ModelCheckpoint

# 1. Cargar y preprocesar los datos
# Supongamos que los datos están en un archivo 'satellite_data.csv' con columnas 'Time', 'latitude', 'longitude'
data = pd.read_csv('historical/historical.csv')

# Normalizar los datos
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['latitude', 'longitude']])

# Crear ventanas de tiempo para la RNN LSTM
def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - time_step - 1):
        a = dataset[i:(i + time_step), :]
        dataX.append(a)
        dataY.append(dataset[i + time_step, :])
    return np.array(dataX), np.array(dataY)

time_step = 5
X, y = create_dataset(scaled_data, time_step)

# Dividir los datos en conjuntos de entrenamiento y prueba
train_size = int(len(X) * 0.7)
test_size = len(X) - train_size
X_train, X_test = X[0:train_size], X[train_size:len(X)]
y_train, y_test = y[0:train_size], y[train_size:len(y)]

# 2. Definir y entrenar el modelo RNN LSTM
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 2)))
model.add(LSTM(50, return_sequences=True))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(2))

model.compile(optimizer='adam', loss='mean_squared_error')

# Guardar el mejor modelo durante el entrenamiento
checkpoint = ModelCheckpoint('best_model.keras', monitor='val_loss', save_best_only=True, mode='min')

# Entrenar el modelo
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=100, batch_size=64, verbose=1, callbacks=[checkpoint])

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

# 4. Plotting de los resultados
plt.figure(figsize=(14, 7))

# Plotear los datos históricos
plt.plot(data['longitude'], data['latitude'], label='Historico', color='red', linestyle='--')
plt.plot(validated_train_predict[:, 1], validated_train_predict[:, 0], label='Entrenamiento', linestyle='dotted')
plt.plot(validated_test_predict[:, 1], validated_test_predict[:, 0], label='Prueba')

plt.xlabel('Tiempo')
plt.ylabel('Posición')
plt.legend()
plt.show()

# 5. Exportación del modelo
model.save('30_seconds_historical_final_4.keras')
