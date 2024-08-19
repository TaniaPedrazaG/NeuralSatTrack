import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score

data = pd.read_csv('ISS (ZARYA).csv')

data['timestamp'] = pd.to_datetime(data['timestamp'])

data = data.sort_values('timestamp')

latitudes = data['latitude'].values
longitudes = data['longitude'].values

scaler_lat = MinMaxScaler(feature_range=(-1, 1))
latitudes_scaled = scaler_lat.fit_transform(latitudes.reshape(-1, 1))

longitudes_rad = np.deg2rad(longitudes)
longitudes_sin = np.sin(longitudes_rad)
longitudes_cos = np.cos(longitudes_rad)

scaler_lon_sin = MinMaxScaler(feature_range=(-1, 1))
scaler_lon_cos = MinMaxScaler(feature_range=(-1, 1))

longitudes_sin_scaled = scaler_lon_sin.fit_transform(longitudes_sin.reshape(-1, 1))
longitudes_cos_scaled = scaler_lon_cos.fit_transform(longitudes_cos.reshape(-1, 1))

def create_sequences(data, seq_length):
    sequences = []
    for i in range(len(data) - seq_length):
        sequences.append(data[i:i + seq_length])
    return np.array(sequences)

SEQ_LENGTH = 50

lat_sequences = create_sequences(latitudes_scaled, SEQ_LENGTH)
sin_sequences = create_sequences(longitudes_sin_scaled, SEQ_LENGTH)
cos_sequences = create_sequences(longitudes_cos_scaled, SEQ_LENGTH)

lat_labels = latitudes_scaled[SEQ_LENGTH:]
sin_labels = longitudes_sin_scaled[SEQ_LENGTH:]
cos_labels = longitudes_cos_scaled[SEQ_LENGTH:]

assert lat_sequences.shape[0] == lat_labels.shape[0]
assert sin_sequences.shape[0] == sin_labels.shape[0]
assert cos_sequences.shape[0] == cos_labels.shape[0]

train_size = int(len(lat_sequences) * 0.8)

X_train_lat, X_test_lat = lat_sequences[:train_size], lat_sequences[train_size:]
y_train_lat, y_test_lat = lat_labels[:train_size], lat_labels[train_size:]

X_train_sin, X_test_sin = sin_sequences[:train_size], sin_sequences[train_size:]
y_train_sin, y_test_sin = sin_labels[:train_size], sin_labels[train_size:]

X_train_cos, X_test_cos = cos_sequences[:train_size], cos_sequences[train_size:]
y_train_cos, y_test_cos = cos_labels[:train_size], cos_labels[train_size:]

def create_gru_model(input_shape):
    model = Sequential()
    model.add(GRU(50, return_sequences=True, input_shape=input_shape))
    model.add(GRU(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

model_lat = create_gru_model((SEQ_LENGTH, 1))
model_sin = create_gru_model((SEQ_LENGTH, 1))
model_cos = create_gru_model((SEQ_LENGTH, 1))

model_lat.fit(X_train_lat, y_train_lat, epochs=50, batch_size=128, validation_split=0.2)

model_sin.fit(X_train_sin, y_train_sin, epochs=50, batch_size=128, validation_split=0.2)

model_cos.fit(X_train_cos, y_train_cos, epochs=50, batch_size=128, validation_split=0.2)

lat_predictions_scaled = model_lat.predict(X_test_lat)
sin_predictions_scaled = model_sin.predict(X_test_sin)
cos_predictions_scaled = model_cos.predict(X_test_cos)

lat_predictions = scaler_lat.inverse_transform(lat_predictions_scaled)
sin_predictions = scaler_lon_sin.inverse_transform(sin_predictions_scaled)
cos_predictions = scaler_lon_cos.inverse_transform(cos_predictions_scaled)

longitudes_predictions_rad = np.arctan2(sin_predictions, cos_predictions)
longitudes_predictions = np.rad2deg(longitudes_predictions_rad)

lat_mse = model_lat.evaluate(X_test_lat, y_test_lat)
sin_mse = model_sin.evaluate(X_test_sin, y_test_sin)
cos_mse = model_cos.evaluate(X_test_cos, y_test_cos)
print(f'Latitud MSE: {lat_mse}')
print(f'Sin MSE: {sin_mse}')
print(f'Cos MSE: {cos_mse}')

lat_rmse = np.sqrt(lat_mse)
sin_rmse = np.sqrt(sin_mse)
cos_rmse = np.sqrt(cos_mse)
print(f"RMSE: {lat_rmse}")
print(f"RMSE: {sin_rmse}")
print(f"RMSE: {cos_rmse}")

lat_r2 = r2_score(y_test_lat, lat_predictions_scaled)
sin_r2 = r2_score(y_test_sin, sin_predictions_scaled)
cos_r2 = r2_score(y_test_cos, cos_predictions_scaled)
print(f'Latitud R²: {lat_r2}')
print(f'Sin R²: {sin_r2}')
print(f'Cos R²: {cos_r2}')