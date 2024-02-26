import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from datetime import datetime

class ISS_TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Tracker")

        # Frame para el lienzo del mapa
        self.map_frame = tk.Frame(self.root)
        self.map_frame.pack(padx=10, pady=10)

        # Inicialización del mapa base
        self.fig = plt.Figure(figsize=(10, 5))
        self.map_ax = self.fig.add_subplot(1, 1, 1)

        # Configuración del mapa
        self.world_map = Basemap(projection='mill', llcrnrlat=-80, urcrnrlat=80, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=self.map_ax)
        self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='royalblue', zorder=None, ax=None)
        self.world_map.fillcontinents(color='forestgreen',lake_color='royalblue')
        self.world_map.drawparallels(range(-90, 91, 30), labels=[1, 0, 0, 0], linewidth=0.5)
        self.world_map.drawmeridians(range(-180, 181, 45), labels=[0, 0, 0, 1], linewidth=0.5)
        date = datetime.utcnow()
        self.world_map.nightshade(date)


        # Canvas para mostrar el mapa
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Botón para iniciar la animación
        self.start_button = tk.Button(self.root, text="Iniciar", command=self.start_animation)
        self.start_button.pack(pady=5)

        # Lista para almacenar las posiciones anteriores de la ISS
        self.iss_positions = []

        # Función de inicialización de la animación
        def init():
            return []

        # Función para verificar si la trayectoria cruza el borde derecho hacia el izquierdo
        def crosses_antimeridian(lon1, lon2):
            return abs(lon1 - lon2) > 180

        # Función de actualización de la animación
        def update(frame):
            self.map_ax.clear()
            self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='royalblue', zorder=None, ax=None)
            self.world_map.fillcontinents(color='forestgreen',lake_color='royalblue')
            self.world_map.drawparallels(range(-90, 91, 30), labels=[1, 0, 0, 0], linewidth=0.5)
            self.world_map.drawmeridians(range(-180, 181, 45), labels=[0, 0, 0, 1], linewidth=0.5)
            date = datetime.utcnow()
            self.world_map.nightshade(date)

            # Obtener la posición actual de la ISS
            lat, lon = self.get_iss_position()
            self.iss_positions.append((lat, lon))
            
            # Dibujar la trayectoria de la ISS
            if len(self.iss_positions) > 1:
                lats, lons = zip(*self.iss_positions)
                x, y = self.world_map(list(lons), list(lats))
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    self.world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-')

            # Dibujar la posición actual de la ISS en el mapa
            x, y = self.world_map(lon, lat)
            self.world_map.plot(x, y, 'wo', markersize=5)

        # Crear la animación
        self.ani = FuncAnimation(self.fig, update, frames=range(100), init_func=init, blit=False, interval=1000)

    # Función para obtener los datos de posición de la ISS en tiempo real
    def get_iss_position(self):
        url = 'http://api.open-notify.org/iss-now.json'
        response = requests.get(url)
        data = response.json()
        position = (float(data['iss_position']['latitude']), float(data['iss_position']['longitude']))
        return position

    # Función para iniciar la animación
    def start_animation(self):
        self.ani.event_source.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ISS_TrackerApp(root)
    root.mainloop()
