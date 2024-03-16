import time
import json
import ephem
import requests
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        selected_index = self.current()
        if selected_index >= 0:
            selected_value = self._completion_list[selected_index]
            selected_satellite = selected_value
            global app
            app.clear_trajectory()

class ISS_TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Tracker")
        self.root.attributes('-zoomed', True)
        self.root.config(bg="#F8F8F8") 

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

        # Frame para el selector de búsqueda con scroll
        self.checkbox_frame = tk.Frame(self.root)
        self.checkbox_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.checkbox_frame.config(bg="red") 

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

        # Variable global para almacenar los satélites seleccionados
        global selected_satellites
        selected_satellites = {}

        # Crear un Canvas para el selector de búsqueda con scroll
        self.canvas = tk.Canvas(self.checkbox_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Agregar un Scrollbar al Canvas
        self.scrollbar = tk.Scrollbar(self.checkbox_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="nsew")
        self.canvas.config(bg="#F8F8F8") 
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame interior para los elementos del Canvas
        self.checkbox_frame_inner = tk.Frame(self.canvas)

        self.checkbox_frame_inner.config(bg="#000000") 
        self.canvas.create_window((0, 0), window=self.checkbox_frame_inner, anchor=tk.NW)

        # Crear Checkbuttons para cada satélite
        self.checkbox_vars = {}
        for i, satellite in enumerate(satelliteList):
            var = tk.BooleanVar(value=False)
            self.checkbox_vars[satellite["satellite_name"]] = var
            checkbox = tk.Checkbutton(self.checkbox_frame_inner, text=satellite["satellite_name"], variable=var)
            checkbox.grid(row=i, column=0, sticky="w")
            checkbox.config(bg="#F8F8F8") 
            checkbox.bind("<Button-1>", self.on_checkbox_click)

        # Panel para mostrar información del satélite
        self.satellite_info_panel = tk.Frame(self.checkbox_frame_inner)
        self.satellite_info_panel.grid(row=len(satelliteList), column=0, sticky="nsew", pady=10)

        # Etiquetas para mostrar la información del satélite
        self.longitude_label = tk.Label(self.satellite_info_panel, text="Longitude:")
        self.longitude_label.grid(row=0, column=0, sticky="e")
        self.latitude_label = tk.Label(self.satellite_info_panel, text="Latitude:")
        self.latitude_label.grid(row=1, column=0, sticky="e")
        self.direction_label = tk.Label(self.satellite_info_panel, text="Direction:")
        self.direction_label.grid(row=2, column=0, sticky="e")
        self.altitude_label = tk.Label(self.satellite_info_panel, text="Altitude (km):")
        self.altitude_label.grid(row=3, column=0, sticky="e")

        # Variables para almacenar la información del satélite seleccionado
        self.longitude_var = tk.StringVar()
        self.latitude_var = tk.StringVar()
        self.direction_var = tk.StringVar()
        self.altitude_var = tk.StringVar()

        # Etiquetas para mostrar la información del satélite seleccionado
        self.longitude_info_label = tk.Label(self.satellite_info_panel, textvariable=self.longitude_var)
        self.longitude_info_label.grid(row=0, column=1, sticky="w")
        self.latitude_info_label = tk.Label(self.satellite_info_panel, textvariable=self.latitude_var)
        self.latitude_info_label.grid(row=1, column=1, sticky="w")
        self.direction_info_label = tk.Label(self.satellite_info_panel, textvariable=self.direction_var)
        self.direction_info_label.grid(row=2, column=1, sticky="w")
        self.altitude_info_label = tk.Label(self.satellite_info_panel, textvariable=self.altitude_var)
        self.altitude_info_label.grid(row=3, column=1, sticky="w") 

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

        global selected_satellite
        selected_satellite = {
            'satellite_name': 'FACSAT-2',
            'line_1': '1 56204U 23054AC  23334.73653880  .00010712  00000+0  42191-3 0  9996',
            'line_2': '2 56204  97.3879 227.5990 0013876 138.1327 222.0975 15.25695519 35559'
            }

        # Función de actualización de la animación
        def update(frame):
            self.map_ax.clear()
            self.map_ax.set_title(selected_satellite['satellite_name'])
            self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
            self.world_map.drawparallels(range(-90, 91, 30), labels=[1, 0, 0, 0], linewidth=0.5)
            self.world_map.drawmeridians(range(-180, 181, 45), labels=[0, 0, 0, 1], linewidth=0.5)
            date = datetime.utcnow()
            self.world_map.nightshade(date)

            # Obtener la posición actual de la ISS
            lat, lon = self.get_sat_position()
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
    def get_sat_position(self):
        global selected_satellite
        self.satellite_name = selected_satellite['satellite_name']
        self.line1 = selected_satellite['line_1']
        self.line2 = selected_satellite['line_2']

        # Crear un objeto satélite
        satellite = ephem.readtle(self.satellite_name, self.line1, self.line2)

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

    def clear_trajectory(self):
        self.iss_positions.clear()

    def on_checkbox_click(self, event):
        global selected_satellites
        for satellite_name, var in self.checkbox_vars.items():
            selected_satellites[satellite_name] = var.get()
        print("Selected satellites:", selected_satellites)

if __name__ == "__main__":
    root = tk.Tk()
    app = ISS_TrackerApp(root)
    root.mainloop()
