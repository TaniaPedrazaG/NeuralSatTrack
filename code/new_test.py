import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# Configuración inicial
num_predictions = 50

# Cargar datos del CSV
df = pd.read_csv('training/data.csv')
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# Asegurarnos que las latitudes y longitudes estén en los rangos especificados
df['latitude'] = df['latitude'].clip(-90, 90)
df['longitude'] = df['longitude'].clip(-180, 180)

# Escalar los datos
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(df)

# Preparar datos para la LSTM
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step - 1):
        X.append(data[i:(i + time_step), :])
        y.append(data[i + time_step, :])
    return np.array(X), np.array(y)

time_step = 20
X, y = create_dataset(scaled_data, time_step)

# Crear el modelo LSTM
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 2)))
model.add(LSTM(50, return_sequences=True))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(2))
model.compile(optimizer='adam', loss='mean_squared_error')

# Entrenar el modelo
model.fit(X, y, epochs=100, batch_size=64, verbose=1)

# Hacer predicciones
predictions = []
input_data = scaled_data[-time_step:].reshape(1, time_step, 2)

for _ in range(num_predictions):
    predicted = model.predict(input_data)
    predictions.append(predicted)
    input_data = np.append(input_data[:, 1:, :], predicted.reshape(1, 1, 2), axis=1)

# Invertir la escala de las predicciones
predictions = scaler.inverse_transform(np.array(predictions).reshape(num_predictions, 2))

# Convertir las predicciones a DataFrame
predictions_df = pd.DataFrame(predictions, columns=['latitude', 'longitude'])
predictions_df['latitude'] = predictions_df['latitude'].clip(-90, 90)
predictions_df['longitude'] = predictions_df['longitude'].clip(-180, 180)

# Crear una columna de tiempo para las predicciones
last_time = df.index[-1]
time_deltas = pd.to_timedelta(np.arange(1, num_predictions + 1), unit='s')
predictions_df['time'] = last_time + time_deltas

# Guardar las predicciones en un archivo CSV
predictions_df.to_csv('iss_position_predictions.csv', index=False)

# Mostrar las predicciones
print(predictions_df)

# Graficar resultados
plt.figure(figsize=(10, 5))

plt.plot(df['longitude'].values, df['latitude'].values, label='Real Path', color='blue')
plt.plot(predictions_df['longitude'].values, predictions_df['latitude'].values, label='Predicted Path', color='red', linestyle='--')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.legend()
plt.title('ISS Position Prediction')
plt.show()