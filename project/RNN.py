import pandas as pd
from math import sqrt, pi
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import SimpleRNN, Dense

GM = 398600.8

file_path = "data/tle_data.json"
df = pd.read_json(file_path)

# Remove unnecesary cols on transformed df
tle_data = df.drop(columns=['satellite_name', 'tle_1', 'tle_2'])

# Split tle_1 column
tle_data['Numero_linea_1'] = df['tle_1'].str.slice(0, 1)
tle_data['Catalogo_1'] = df['tle_1'].str.slice(2, 7)
tle_data['Clasificacion'] = df['tle_1'].str.slice(7, 8)
tle_data['Identificacion'] = df['tle_1'].str.slice(9, 15)
tle_data['Año'] = df['tle_1'].str.slice(18, 20)
tle_data['Dia'] = df['tle_1'].str.slice(20, 23)
tle_data['Fraccion_dia'] = df['tle_1'].str.slice(23, 32)
tle_data['Signo_derivada_1'] = df['tle_1'].str.slice(33, 34)
tle_data['Derivada_1'] = df['tle_1'].str.slice(34, 43)
tle_data['Signo_derivada_2'] = df['tle_1'].str.slice(44, 45)
tle_data['Derivada_2'] = df['tle_1'].str.slice(45, 50)
tle_data['Exponente'] = df['tle_1'].str.slice(50, 52)
tle_data['Signo_BSTAR'] = df['tle_1'].str.slice(53, 54)
tle_data['BSTAR'] = df['tle_1'].str.slice(54, 59)
tle_data['Exponente_BSTAR'] = df['tle_1'].str.slice(59, 61)
tle_data['Efemerides'] = df['tle_1'].str.slice(62, 63)
tle_data['Numero_elemento'] = df['tle_1'].str.slice(64, 68)
tle_data['Checksum_1'] = df['tle_1'].str.slice(68, 69)

# Split tle_2 column
tle_data['Numero_linea_2'] = df['tle_2'].str.slice(0, 1)
tle_data['Catalogo_2'] = df['tle_2'].str.slice(2, 7)
tle_data['Inclinacion'] = df['tle_2'].str.slice(8, 16).astype(float, errors='raise')
tle_data['Ascencion'] = df['tle_2'].str.slice(17, 25).astype(float, errors='raise')
tle_data['Excentricidad'] = ('0.' + df['tle_2'].str.slice(26, 33)).astype(float, errors='raise')
tle_data['Perigeo'] = df['tle_2'].str.slice(34, 42).astype(float, errors='raise')
tle_data['Anomalia_media'] = df['tle_2'].str.slice(43, 51).astype(float, errors='raise')
tle_data['Revoluciones_dia'] = df['tle_2'].str.slice(52, 63).astype(float, errors='raise')
tle_data['Revoluciones_epoch'] = df['tle_2'].str.slice(63, 68).astype(float, errors='raise')
tle_data['Checksum_2'] = df['tle_2'].str.slice(68, 69)

def calcPeriod():
    T = 86400 / tle_data['Revoluciones_dia']
    return round(T, 10)
tle_data['Periodo'] = calcPeriod()
tle_data['Periodo'] = tle_data['Periodo'].astype(float, errors='raise')

def calcMajorSemiaxis():
    major_semiaxis = ((GM*(tle_data['Periodo']**2))/(4 * (pi**2)))**(1/3)
    return round(major_semiaxis, 10)
tle_data['Semieje_mayor'] = calcMajorSemiaxis()
tle_data['Semieje_mayor'] = tle_data['Semieje_mayor'].astype(float, errors='raise')

def calcMinorSemiaxis():
    minor_semiaxis = (tle_data['Semieje_mayor'])*(sqrt(1-(tle_data['Excentricidad'].iloc[0]**2)))
    return round(minor_semiaxis, 10)
tle_data['Semieje_menor'] = calcMinorSemiaxis()
tle_data['Semieje_menor'] = tle_data['Semieje_menor'].astype(float, errors='raise')

tle_data.to_csv('data/tle_transformed.csv', encoding='utf-8')

# Genera datos de ejemplo (necesitarás datos reales de órbitas satelitales)
def generate_sample_data(num_samples, input_length):
    # Aquí deberías cargar tus datos reales de órbitas satelitales
    # y preprocesarlos adecuadamente.
    data = np.random.rand(num_samples, input_length, 3)  # Datos de ejemplo
    labels = np.random.rand(num_samples, 3)  # Etiquetas de ejemplo
    return data, labels

# Parámetros
num_samples = 1000
input_length = 10
hidden_units = 64

# Genera datos de ejemplo
data, labels = generate_sample_data(num_samples, input_length)

# Construye el modelo RNN
model = Sequential([
    SimpleRNN(hidden_units, input_shape=(input_length, 3), activation='relu'),
    Dense(3)  # La capa de salida tiene 3 unidades para predecir las coordenadas x, y, z
])

# Compila el modelo
model.compile(optimizer='adam', loss='mean_squared_error')

# Entrena el modelo
model.fit(data, labels, epochs=10, batch_size=32)

# Ahora puedes usar el modelo entrenado para hacer predicciones en nuevas secuencias.
# Ten en cuenta que este es un ejemplo muy básico y no representa una solución completa
# para el problema de predicción de órbitas satelitales, que es bastante complejo.

