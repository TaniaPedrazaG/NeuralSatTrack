import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from sklearn.preprocessing import MinMaxScaler

df = pd.read_csv('data/historic/historic_data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

df['sin_latitude'] = np.sin(np.radians(df['latitude']))
df['cos_latitude'] = np.cos(np.radians(df['latitude']))
df['sin_longitude'] = np.sin(np.radians(df['longitude']))
df['cos_longitude'] = np.cos(np.radians(df['longitude']))

scaler_sin_lat = MinMaxScaler(feature_range=(-1, 1))
scaler_cos_lat = MinMaxScaler(feature_range=(-1, 1))
scaler_sin_lon = MinMaxScaler(feature_range=(-1, 1))
scaler_cos_lon = MinMaxScaler(feature_range=(-1, 1))

df['sin_latitude'] = scaler_sin_lat.fit_transform(df[['sin_latitude']])
df['cos_latitude'] = scaler_cos_lat.fit_transform(df[['cos_latitude']])
df['sin_longitude'] = scaler_sin_lon.fit_transform(df[['sin_longitude']])
df['cos_longitude'] = scaler_cos_lon.fit_transform(df[['cos_longitude']])

def create_sequences(data, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data.iloc[i:(i + seq_length)][['sin_latitude', 'cos_latitude', 'sin_longitude', 'cos_longitude']].values
        y = data.iloc[i + seq_length][['sin_latitude', 'cos_latitude', 'sin_longitude', 'cos_longitude']].values
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

SEQ_LENGTH = 80
X, y = create_sequences(df, SEQ_LENGTH)

split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

model = Sequential([
    GRU(256, activation='relu', input_shape=(SEQ_LENGTH, 4), return_sequences=True, kernel_regularizer=l2(0.001)),
    Dropout(0.4),
    GRU(256, activation='relu', kernel_regularizer=l2(0.001)),
    Dropout(0.4),
    Dense(128, activation='relu', kernel_regularizer=l2(0.001)),
    Dropout(0.4),
    Dense(4)
])

def custom_loss(y_true, y_pred):
    sin_lat_loss = tf.reduce_mean(tf.square(y_true[:, 0] - y_pred[:, 0]))
    cos_lat_loss = tf.reduce_mean(tf.square(y_true[:, 1] - y_pred[:, 1]))
    sin_lon_loss = tf.reduce_mean(tf.square(y_true[:, 2] - y_pred[:, 2]))
    cos_lon_loss = tf.reduce_mean(tf.square(y_true[:, 3] - y_pred[:, 3]))
    return sin_lat_loss + cos_lat_loss + sin_lon_loss + cos_lon_loss

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss=custom_loss)

early_stopping = EarlyStopping(monitor='val_loss', patience=30, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=15, min_lr=0.00001)

history = model.fit(X_train, y_train, validation_split=0.2, epochs=500, batch_size=128, callbacks=[early_stopping, reduce_lr])

model.save('GRU_model.keras')
joblib.dump(scaler_sin_lat, 'scaler_sin_lat.pkl')
joblib.dump(scaler_cos_lat, 'scaler_cos_lat.pkl')
joblib.dump(scaler_sin_lon, 'scaler_sin_lon.pkl')
joblib.dump(scaler_cos_lon, 'scaler_cos_lon.pkl')

model.evaluate(X_test, y_test)
