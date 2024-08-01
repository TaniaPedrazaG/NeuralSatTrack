import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

# Cargar los datos desde el CSV
data = pd.read_csv('data.csv', parse_dates=['time'])

# Escalar los datos
scaler_lat = MinMaxScaler(feature_range=(-90, 90))
scaler_lon = MinMaxScaler(feature_range=(-180, 180))
data['latitude'] = scaler_lat.fit_transform(data['latitude'].values.reshape(-1, 1))
data['longitude'] = scaler_lon.fit_transform(data['longitude'].values.reshape(-1, 1))

# Crear dataset para la LSTM
def create_dataset(dataset, look_back=1):
    X, Y_lat, Y_lon = [], [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), :]
        X.append(a)
        Y_lat.append(dataset[i + look_back, 0])
        Y_lon.append(dataset[i + look_back, 1])
    return np.array(X), np.array(Y_lat), np.array(Y_lon)

# Convertir los datos a un numpy array
dataset = data[['latitude', 'longitude']].values

# Dividir los datos en conjuntos de entrenamiento y prueba
train_size = int(len(dataset) * 0.6)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size], dataset[train_size:len(dataset)]

# Crear el dataset con una ventana de tiempo (look_back)
look_back = 20
X_train, y_train_lat, y_train_lon = create_dataset(train, look_back)
X_test, y_test_lat, y_test_lon = create_dataset(test, look_back)

# Reshape input to be [samples, time steps, features]
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 2))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 2))

# Crear el modelo LSTM
model = Sequential()
model.add(LSTM(50, input_shape=(look_back, 2)))
model.add(Dropout(0.2))
model.add(Dense(2))  # Salida para latitud y longitud
model.compile(loss='mean_squared_error', optimizer='adam')

# Configurar el EarlyStopping
early_stop = EarlyStopping(monitor='val_loss', patience=10)

# Entrenar el modelo
history = model.fit(X_train, np.column_stack((y_train_lat, y_train_lon)), epochs=100, batch_size=64, validation_data=(X_test, np.column_stack((y_test_lat, y_test_lon))), callbacks=[early_stop], verbose=2)

# Hacer predicciones
predictions = model.predict(X_test)

# Invertir las predicciones para tener los valores originales
predictions[:, 0] = scaler_lat.inverse_transform(predictions[:, 0].reshape(-1, 1)).reshape(-1)
predictions[:, 1] = scaler_lon.inverse_transform(predictions[:, 1].reshape(-1, 1)).reshape(-1)

# Invertir los valores reales para compararlos con las predicciones
y_test_lat = scaler_lat.inverse_transform(y_test_lat.reshape(-1, 1)).reshape(-1)
y_test_lon = scaler_lon.inverse_transform(y_test_lon.reshape(-1, 1)).reshape(-1)

# Filtrar los resultados fuera de rango
filtered_predictions = [(lat, lon) for lat, lon in predictions if -90 <= lat <= 90 and -180 <= lon <= 180]

# Convertir a un DataFrame para mejor visualización
filtered_predictions_df = pd.DataFrame(filtered_predictions, columns=['latitude', 'longitude'])

# Filtrar los valores reales correspondientes
valid_indices = [i for i, (lat, lon) in enumerate(predictions) if -90 <= lat <= 90 and -180 <= lon <= 180]
filtered_y_test_lat = y_test_lat[valid_indices]
filtered_y_test_lon = y_test_lon[valid_indices]

# Ploteo de los resultados
plt.figure(figsize=(14, 7))

# Plotear longitud
plt.subplot(2, 1, 2)
plt.plot(filtered_y_test_lon, filtered_y_test_lat, label='Actual')
plt.plot(filtered_predictions_df['longitude'].values, filtered_predictions_df['latitude'].values, label='Predicted')
plt.title('Longitude Prediction')
plt.xlabel('Time Step')
plt.ylabel('Longitude')
plt.legend()

plt.tight_layout()
plt.show()

# Guardar el modelo para uso futuro
model.save('position_model.h5')
