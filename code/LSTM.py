import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# Supongamos que 'data' es un DataFrame con las columnas 'time', 'longitude' y 'latitude'
data = pd.read_csv('historical/history_positions.csv')
data['time'] = pd.to_datetime(data['time'])

# Normalizar datos
scaler = MinMaxScaler(feature_range=(0, 1))
data[['longitude', 'latitude']] = scaler.fit_transform(data[['longitude', 'latitude']])

# Crear secuencias de entrada y salida para el modelo LSTM
sequence_length = 50
def create_sequences(data, sequence_length):
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i+sequence_length])
        y.append(data[i+sequence_length])
    return np.array(X), np.array(y)

X, y = create_sequences(data[['longitude', 'latitude']].values, sequence_length)

# Dividir en conjuntos de entrenamiento y prueba
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Crear el modelo LSTM
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(sequence_length, 2)))
model.add(LSTM(50))
model.add(Dense(2))

model.compile(optimizer='adam', loss='mean_squared_error')

# Entrenar el modelo
model.fit(X_train, y_train, epochs=20, batch_size=64, validation_data=(X_test, y_test))

# Predicción de los siguientes valores
last_sequence = X_test[-1]  # Utilizar la última secuencia del conjunto de prueba para predecir
predictions = []
for _ in range(50):  # Predecir 50 pasos futuros
    next_value = model.predict(np.expand_dims(last_sequence, axis=0))
    predictions.append(next_value[0])
    last_sequence = np.append(last_sequence[1:], next_value, axis=0)

# Desnormalizar los datos predichos
predictions = scaler.inverse_transform(predictions)

model.save('models/model_1.keras')