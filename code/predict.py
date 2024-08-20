import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

from satelliteCalculated import *

def predict_values(selected_satellite):
    
    sat_name = selected_satellite['satellite_name']
    
    def create_sequences(data, seq_length):
        sequences = []
        for i in range(len(data) - seq_length):
            sequences.append(data[i:i + seq_length])
        return np.array(sequences)
    
    model_lat = load_model('model/model_lat.keras')
    model_sin = load_model('model/model_sin.keras')
    model_cos = load_model('model/model_cos.keras')
    
    new_data = pd.read_csv('data/historic/' + sat_name +'.csv')
    
    new_data['timestamp'] = pd.to_datetime(new_data['timestamp'])
    
    latitudes = new_data['latitude'].values
    longitudes = new_data['longitude'].values
    
    scaler_lat = MinMaxScaler(feature_range=(-1, 1))
    latitudes_scaled = scaler_lat.fit_transform(latitudes.reshape(-1, 1))
    
    longitudes_rad = np.deg2rad(longitudes)
    longitudes_sin = np.sin(longitudes_rad)
    longitudes_cos = np.cos(longitudes_rad)
    
    scaler_lon_sin = MinMaxScaler(feature_range=(-1, 1))
    scaler_lon_cos = MinMaxScaler(feature_range=(-1, 1))

    longitudes_sin_scaled = scaler_lon_sin.fit_transform(longitudes_sin.reshape(-1, 1))
    longitudes_cos_scaled = scaler_lon_cos.fit_transform(longitudes_cos.reshape(-1, 1))
    
    SEQ_LENGTH = 50

    lat_sequences = create_sequences(latitudes_scaled, SEQ_LENGTH)
    sin_sequences = create_sequences(longitudes_sin_scaled, SEQ_LENGTH)
    cos_sequences = create_sequences(longitudes_cos_scaled, SEQ_LENGTH)
    
    lat_predictions_scaled = model_lat.predict(lat_sequences)
    sin_predictions_scaled = model_sin.predict(sin_sequences)
    cos_predictions_scaled = model_cos.predict(cos_sequences)
    
    lat_predictions = scaler_lat.inverse_transform(lat_predictions_scaled)
    sin_predictions = scaler_lon_sin.inverse_transform(sin_predictions_scaled)
    cos_predictions = scaler_lon_cos.inverse_transform(cos_predictions_scaled)
    
    longitudes_predictions_rad = np.arctan2(sin_predictions, cos_predictions)
    longitudes_predictions = np.rad2deg(longitudes_predictions_rad)

    results_df = pd.DataFrame({
        'timestamp': new_data['timestamp'][SEQ_LENGTH:].values,
        'latitude_predicted': lat_predictions.flatten(),
        'longitude_predicted': longitudes_predictions.flatten()
    })
    
    predicted_values = []
    for index, row in results_df.iterrows():
        azimut = calc_azimut(row['longitude_predicted'])
        predicted_values.append([row['timestamp'], row['longitude_predicted'], row['latitude_predicted'], azimut])

    return predicted_values
