from math import sqrt, pi
import numpy as np
import tensorflow
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import SimpleRNN, Dense

class RNNPrediction:
    def __init__(self):
        pass

    def predict_orbit(self, satellite_tle):
        GM = 398600.8

        numero_linea_1 = satellite_tle['line_1'][:1]
        catalogo_1 = satellite_tle['line_1'][2:7]
        clasificacion = satellite_tle['line_1'][7:8]
        identificacion = satellite_tle['line_1'][9:15]
        año = satellite_tle['line_1'][18:20]
        dia = satellite_tle['line_1'][20:23]
        fraccion_dia = satellite_tle['line_1'][23:32]
        signo_derivada_1 = satellite_tle['line_1'][33:34]
        derivada_1 = satellite_tle['line_1'][34:43]
        signo_derivada_2 = satellite_tle['line_1'][44:45]
        derivada_2 = satellite_tle['line_1'][45:50]
        exponente = satellite_tle['line_1'][50:52]
        signo_BSTAR = satellite_tle['line_1'][53:54]
        bstar = satellite_tle['line_1'][54:59]
        exponente_BSTAR = satellite_tle['line_1'][59:61]
        efemerides = satellite_tle['line_1'][62:63]
        numero_elemento = satellite_tle['line_1'][64:68]
        checksum_1 = satellite_tle['line_1'][68:69]

        # Split tle_2 column
        numero_linea_2 = satellite_tle['line_2'][0:1]
        catalogo_2 = satellite_tle['line_2'][2:7]
        inclinacion = satellite_tle['line_2'][8:16]
        ascencion = satellite_tle['line_2'][17:25]
        excentricidad = ('0.' + satellite_tle['line_2'][26:33])
        perigeo = satellite_tle['line_2'][34:42]
        anomalia_media = satellite_tle['line_2'][43:51]
        revoluciones_dia = satellite_tle['line_2'][52:63]
        revoluciones_epoch = satellite_tle['line_2'][63:68]
        checksum_2 = satellite_tle['line_2'][68:69]

        def calcPeriod():
            T = 86400 / float(revoluciones_dia)
            return round(T, 10)
        Periodo = calcPeriod()
        Periodo = Periodo

        def calcMajorSemiaxis():
            major_semiaxis = ((GM*(Periodo**2))/(4 * (pi**2)))**(1/3)
            return round(major_semiaxis, 10)
        Semieje_mayor = calcMajorSemiaxis()
        Semieje_mayor = Semieje_mayor

        def calcMinorSemiaxis():
            minor_semiaxis = (Semieje_mayor)*(sqrt(1 - float(excentricidad)))
            return round(minor_semiaxis, 10)
        Semieje_menor = calcMinorSemiaxis()
        Semieje_menor = Semieje_menor

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
