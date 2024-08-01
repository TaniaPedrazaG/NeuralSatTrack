from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timedelta
import csv

# Cargar timescale
ts = load.timescale()

# Datos del satélite ISS (ZARYA)
satellite_name = 'ISS (ZARYA)'
line1 = '1 25544U 98067A   24209.53295808  .00020854  00000+0  36733-3 0  9990'
line2 = '2 25544  51.6395 115.4502 0009461 111.9570  72.0544 15.50350916464802'
satellite = EarthSatellite(line1, line2, satellite_name, ts)

# Definir rango de fechas
start_time = datetime(2024, 7, 27, 11, 9, 30)
end_time = datetime(2024, 7, 27, 23, 0, 0)

# Inicializar tiempo actual
current_time = start_time

results = []

while current_time <= end_time:
    # Convertir datetime a tiempo skyfield
    t = ts.utc(current_time.year, current_time.month, current_time.day,
               current_time.hour, current_time.minute, current_time.second)
    
    # Obtener la posición del satélite
    geocentric = satellite.at(t)
    lat, lon = wgs84.latlon_of(geocentric)
    
    # Ajustar el tiempo restando 5 horas
    adjusted_time = current_time - timedelta(hours=5)
    
    results.append((lon.degrees, lat.degrees, adjusted_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    # Incrementar tiempo en 30 segundos
    current_time += timedelta(seconds=30)

with open('historical/history_positions_4.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # Escribir encabezado
    writer.writerow(['Longitud', 'Latitud', 'Tiempo ajustado'])
    # Escribir los datos
    writer.writerows(results)