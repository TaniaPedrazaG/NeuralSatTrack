import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

# 1. Cargar el modelo exportado
model = load_model('models/best_model.keras')

# 2. Cargar y preprocesar el archivo de datos
data = pd.read_csv('historical/history_positions_3.csv')

# Normalizar los datos
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['latitude', 'longitude']])

# Crear ventanas de tiempo para la predicción
def create_dataset(dataset, time_step=1):
    dataX = []
    for i in range(len(dataset) - time_step):
        a = dataset[i:(i + time_step), :]
        dataX.append(a)
    return np.array(dataX)

time_step = 50
X = create_dataset(scaled_data, time_step)

# 3. Generar las predicciones usando el modelo
predictions = model.predict(X)

# Invertir la normalización
predictions = scaler.inverse_transform(predictions)

# 4. Validar las predicciones
def validate_predictions(predictions):
    validated = []
    for pred in predictions:
        if -90 <= pred[0] <= 90 and -180 <= pred[1] <= 180:
            validated.append(pred)
    return np.array(validated)

validated_predictions = validate_predictions(predictions)

# Asegurarse de que las predicciones y los datos históricos tienen la misma longitud para la visualización
pred_start_idx = time_step
pred_end_idx = pred_start_idx + len(validated_predictions)

# 5. Plotear los datos históricos y las predicciones
plt.figure(figsize=(14, 7))

# Datos históricos
plt.plot(data['longitude'], data['latitude'], label='Histórica', color='blue', linestyle='--', alpha=0.6)

# Predicciones
plt.plot(validated_predictions[:, 1], validated_predictions[:, 0], label='Predicción', color='red')

plt.xlabel('Índice de Tiempo')
plt.ylabel('Posición')
plt.title('Datos Históricos vs Predicciones')
plt.legend()
plt.show()

# 6. Guardar las predicciones en un archivo CSV
predictions_df = pd.DataFrame(validated_predictions, columns=['latitude', 'longitude'])
predictions_df.to_csv('predictions.csv', index=False)

print("Predicciones guardadas en 'predictions.csv'")
