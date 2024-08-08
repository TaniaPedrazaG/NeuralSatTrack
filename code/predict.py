import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model

def predict_values(selected_satellite):
    def custom_loss(y_true, y_pred):
        sin_lat_loss = tf.reduce_mean(tf.square(y_true[:, 0] - y_pred[:, 0]))
        cos_lat_loss = tf.reduce_mean(tf.square(y_true[:, 1] - y_pred[:, 1]))
        sin_lon_loss = tf.reduce_mean(tf.square(y_true[:, 2] - y_pred[:, 2]))
        cos_lon_loss = tf.reduce_mean(tf.square(y_true[:, 3] - y_pred[:, 3]))
        return sin_lat_loss + cos_lat_loss + sin_lon_loss + cos_lon_loss
    
    sat_name = selected_satellite['satellite_name']

    model = load_model('model/RNN_GRU_model.keras', custom_objects={'custom_loss': custom_loss})
    scaler_sin_lat = joblib.load('model/scaler_sin_lat.pkl')
    scaler_cos_lat = joblib.load('model/scaler_cos_lat.pkl')
    scaler_sin_lon = joblib.load('model/scaler_sin_lon.pkl')
    scaler_cos_lon = joblib.load('model/scaler_cos_lon.pkl')

    df_new = pd.read_csv('data/historic/' + sat_name + '.csv')
    df_new['timestamp'] = pd.to_datetime(df_new['timestamp'])
    df_new.set_index('timestamp', inplace=True)

    df_new['sin_latitude'] = np.sin(np.radians(df_new['latitude']))
    df_new['cos_latitude'] = np.cos(np.radians(df_new['latitude']))
    df_new['sin_longitude'] = np.sin(np.radians(df_new['longitude']))
    df_new['cos_longitude'] = np.cos(np.radians(df_new['longitude']))

    df_new['sin_latitude'] = scaler_sin_lat.transform(df_new[['sin_latitude']])
    df_new['cos_latitude'] = scaler_cos_lat.transform(df_new[['cos_latitude']])
    df_new['sin_longitude'] = scaler_sin_lon.transform(df_new[['sin_longitude']])
    df_new['cos_longitude'] = scaler_cos_lon.transform(df_new[['cos_longitude']])

    def create_sequences(data, seq_length):
        xs = []
        for i in range(len(data) - seq_length):
            x = data.iloc[i:(i + seq_length)][['sin_latitude', 'cos_latitude', 'sin_longitude', 'cos_longitude']].values
            xs.append(x)
        return np.array(xs)

    SEQ_LENGTH = 80
    X_new = create_sequences(df_new, SEQ_LENGTH)

    predictions = model.predict(X_new)

    pred_sin_lat = scaler_sin_lat.inverse_transform(predictions[:, 0].reshape(-1, 1))
    pred_cos_lat = scaler_cos_lat.inverse_transform(predictions[:, 1].reshape(-1, 1))
    pred_sin_lon = scaler_sin_lon.inverse_transform(predictions[:, 2].reshape(-1, 1))
    pred_cos_lon = scaler_cos_lon.inverse_transform(predictions[:, 3].reshape(-1, 1))

    pred_lat = np.degrees(np.arctan2(pred_sin_lat, pred_cos_lat))
    pred_lon = np.degrees(np.arctan2(pred_sin_lon, pred_cos_lon))

    pred_lat = np.clip(pred_lat, -90, 90)
    pred_lon = np.clip(pred_lon, -180, 180)

    predictions_df = pd.DataFrame({
        'timestamp': df_new.index[SEQ_LENGTH:],
        'predicted_latitude': pred_lat.flatten(),
        'predicted_longitude': pred_lon.flatten()
    })

    df_hist = df_new[['latitude', 'longitude']].iloc[SEQ_LENGTH:]
    predictions_df['actual_latitude'] = df_hist['latitude'].values
    predictions_df['actual_longitude'] = df_hist['longitude'].values

    predictions_df.to_csv('data/predictions/predictions_data.csv', index=False)

    predicted_values = []

    for index, row in predictions_df.iterrows():
        predicted_values.append((row['predicted_longitude'], row['predicted_latitude']))

    return predicted_values
