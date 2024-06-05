import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Constantes
c = 3e8  # Velocidad de la luz en m/s
f = 12e9  # Frecuencia de la señal en Hz
D = 2.0  # Diámetro de la antena en metros
k = 1.22  # Constante para una antena parabólica

# Calcular la longitud de onda
lambda_ = c / f

# Calcular el ángulo del haz en radianes
theta_rad = k * lambda_ / D

# Convertir el ángulo del haz a grados
theta_deg = np.degrees(theta_rad)

print(f"Ángulo del haz: {theta_deg:.3f} grados")

# Radio de la Tierra en km
R_e = 6371.0

# Altitud del satélite en km (por ejemplo, ISS)
h = 400.0

# Calcular el radio de cobertura
R_c = R_e * np.arccos((R_e / (R_e + h)) * np.cos(theta_rad / 2))

# Coordenadas del satélite (latitud y longitud en grados)
lat_sat = 0.0  # Ejemplo: sobre el ecuador
lon_sat = 0.0  # Ejemplo: sobre el meridiano de Greenwich

# Crear un mapa utilizando Basemap
fig, ax = plt.subplots(figsize=(10, 8))
m = Basemap(projection='mill', llcrnrlat=-90, urcrnrlat=90,
            llcrnrlon=-180, urcrnrlon=180, resolution='c')

# Dibujar costas y continentes
m.drawcoastlines()
m.drawcountries()
m.fillcontinents(color='lightgray', lake_color='aqua')

# Dibujar los paralelos y meridianos
m.drawparallels(np.arange(-90., 91., 30.))
m.drawmeridians(np.arange(-180., 181., 60.))
m.drawmapboundary(fill_color='aqua')

# Número de puntos para el contorno del haz
num_points = 100
angles = np.linspace(0, 2 * np.pi, num_points)

# Calcular los puntos del contorno del haz
latitudes = []
longitudes = []
for angle in angles:
    d_lat = np.degrees(R_c / R_e * np.cos(angle))
    d_lon = np.degrees(R_c / R_e * np.sin(angle) / np.cos(np.radians(lat_sat)))
    latitudes.append(lat_sat + d_lat)
    longitudes.append(lon_sat + d_lon)

# Convertir las coordenadas a la proyección del mapa
x, y = m(longitudes, latitudes)

# Dibujar el contorno del haz en el mapa
m.plot(x, y, marker=None, color='red')

# Marcar la posición del satélite
sat_x, sat_y = m(lon_sat, lat_sat)
m.plot(sat_x, sat_y, marker='o', color='blue', markersize=10)

plt.title("Cobertura del haz del satélite")
plt.show()
