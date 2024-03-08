import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
import ephem
import time
from datetime import datetime
import json

class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<<ComboboxSelected>>', self.on_select)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=lambda x: x.get("satellite_name", "").lower())
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = [item["satellite_name"] for item in self._completion_list]

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())
        _hits = []
        for item in self._completion_list:
            if item["satellite_name"].lower().startswith(self.get().lower()):
                _hits.append(item["satellite_name"])
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        if _hits:
            self._hit_index = (self._hit_index + delta) % len(_hits)
            self.delete(0, tk.END)
            self.insert(0, _hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        if event.keysym in ("BackSpace", "Right", "Left", "Shift_L", "Shift_R"):
            return
        if event.keysym == "Down":
            self.autocomplete(1)
        elif event.keysym == "Up":
            self.autocomplete(-1)
        elif event.keysym == "Return":
            self.autocomplete(0)
        else:
            self.autocomplete()

    def on_select(self, event=None):
        global selected_satellite
        selected_satellite = self.get()
        print("Selected value:", selected_satellite)

class ISS_TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Tracker")
        self.root.attributes('-zoomed', True)

        # Frame para el lienzo del mapa
        self.map_frame = tk.Frame(self.root)
        self.map_frame.grid(row=0, column=0)

        # Inicialización del mapa base
        self.fig = plt.Figure(figsize=(15, 8))
        self.map_ax = self.fig.add_subplot(1, 1, 1)

        # Configuración del mapa
        self.world_map = Basemap(projection='gall', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=self.map_ax)
        self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
        self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
        self.world_map.drawparallels(range(-90, 91, 30), labels=[1, 0, 0, 0], linewidth=0.5)
        self.world_map.drawmeridians(range(-180, 181, 45), labels=[0, 0, 0, 1], linewidth=0.5)
        date = datetime.utcnow()
        self.world_map.nightshade(date)

        # Canvas para mostrar el mapa
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Frame para el panel de checkboxes
        self.checkbox_frame = tk.Frame(self.root)
        self.checkbox_frame.grid(row=0, column=1)

        # Variables para almacenar los estados de los checkboxes
        self.checkbox_vars = []

        satelliteList = []
        with open('data/tle_data.json') as f:
            data = json.load(f)

        for satellite in data:
            satelliteList.append({
                "satellite_name": satellite["satellite_name"],
                "line_1": satellite["tle_1"],
                "line_2": satellite["tle_2"]
            })

        # Variable global para almacenar el satélite seleccionado
        global selected_satellite
        selected_satellite = tk.StringVar()

        # Crear un Combobox con funcionalidad de búsqueda
        self.satellite_combobox = AutocompleteCombobox(self.checkbox_frame, textvariable=selected_satellite)
        self.satellite_combobox.set_completion_list(satelliteList)
        self.satellite_combobox.pack(fill=tk.BOTH, expand=True)

        # Botón para iniciar la animación
        self.start_button = tk.Button(self.root, text="Iniciar", command=self.start_animation)
        self.start_button.grid(row=1, column=0, columnspan=2, pady=5)

        # Lista para almacenar las posiciones anteriores de la ISS
        self.iss_positions = []

        # Función de inicialización de la animación
        def init():
            return []

        # Función para verificar si la trayectoria cruza el borde derecho hacia el izquierdo
        def crosses_antimeridian(lon1, lon2):
            return abs(lon1 - lon2) > 180
        
        self.satellite_name = "FACSAT-2"
        self.line1 = "1 56204U 23054AC  23334.73653880  .00010712  00000+0  42191-3 0  9996"
        self.line2 = "2 56204  97.3879 227.5990 0013876 138.1327 222.0975 15.25695519 35559"

        # Función de actualización de la animación
        def update(frame):
            self.map_ax.clear()
            self.map_ax.set_title(self.satellite_name)
            self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
            self.world_map.drawparallels(range(-90, 91, 30), labels=[1, 0, 0, 0], linewidth=0.5)
            self.world_map.drawmeridians(range(-180, 181, 45), labels=[0, 0, 0, 1], linewidth=0.5)
            date = datetime.utcnow()
            self.world_map.nightshade(date)

            # Obtener la posición actual de la ISS
            lat, lon = self.get_sat_position(self.satellite_name, self.line1, self.line2)
            self.iss_positions.append((lat, lon))
            
            # Dibujar la trayectoria de la ISS
            if len(self.iss_positions) > 1:
                lats, lons = zip(*self.iss_positions)
                x, y = self.world_map(list(lons), list(lats))
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    self.world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-', linewidth=0.5)

            # Dibujar la posición actual de la ISS en el mapa
            x, y = self.world_map(lon, lat)
            self.world_map.plot(x, y, 'wo', markersize=5)

        # Crear la animación
        self.ani = FuncAnimation(self.fig, update, frames=range(100), init_func=init, blit=False, interval=1000)

    # Función para obtener los datos de posición de la ISS en tiempo real
    def get_sat_position(self, sat_name, line_1, line_2):
        self.satellite_name = sat_name
        self.line1 = line_1
        self.line2 = line_2

        # Crear un objeto satélite
        satellite = ephem.readtle(sat_name, line_1, line_2)

        # Tiempo inicial
        start_time = time.time()

        satellite.compute()  # Calcular la posición del satélite
        lat = satellite.sublat / ephem.degree  # Latitud en grados
        lon = satellite.sublong / ephem.degree  # Longitud en grados
        position = (float(lat), float(lon))
        return position

    # Función para iniciar la animación
    def start_animation(self):
        self.ani.event_source.start()
        global selected_satellite
        print("Satellite selected:", selected_satellite.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = ISS_TrackerApp(root)
    root.mainloop()
