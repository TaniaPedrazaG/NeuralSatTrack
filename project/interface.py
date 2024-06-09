import json
import datetime
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from ttkbootstrap.constants import *
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from RNN import RNNPrediction
from satelliteCalculated import *

class AppInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("NeuralSatTrack")
        self.root.attributes('-zoomed', True)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.rnn_instance = RNNPrediction()

        et_lon, et_lat = observer_location()

        et_city = 'Sogamoso'

        ttk.Style().configure("TCheckbutton", padding=10, font=('Helvetica', 10))

        satelliteList = []
        with open('data/satnogs.json') as f:
            data = json.load(f)

        for satellite in data:
            satelliteList.append({
                "satellite_name": satellite["satellite_name"],
                "line_1": satellite["tle_1"],
                "line_2": satellite["tle_2"]
            })

        satelliteList_cleaned = [dict(t) for t in {tuple(d.items()) for d in satelliteList}]

        sorted_satelliteList = sorted(satelliteList_cleaned, key=lambda x: x['satellite_name'])

        for i, elemento in enumerate(sorted_satelliteList):
            if elemento['satellite_name'] == 'ISS (ZARYA)':
                position = i
                break
            else:
                position = 0

        global selected_satellite
        selected_satellite = sorted_satelliteList[position]

        # Inicializacion frame para el lienzo del mapa
        self.map_frame = ttk.Frame(root, width=400, height=200)
        self.map_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Inicializacion del mapa base
        self.fig = plt.Figure(figsize=(15, 8))
        self.map_ax = self.fig.add_subplot(1, 1, 1)

        # Configuración del mapa
        self.world_map = Basemap(projection='gall', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=self.map_ax)
        self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
        self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
        self.world_map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
        self.world_map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
        self.date = datetime.datetime.now()
        utc_time = datetime.datetime.utcnow()
        self.world_map.nightshade(utc_time)

        # Inicializacion frame para los controles
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.data_frame = ttk.Frame(root, width=100, height=200, padding=20)
        self.data_frame.grid(row=1, column=0 ,sticky="nsew")

        self.title_label = ttk.Label(self.data_frame, text=selected_satellite['satellite_name'], bootstyle=DARK, justify="center")
        self.title_label.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=2)

        self.separator = ttk.Separator(self.data_frame, bootstyle=DARK)
        self.separator.grid(row=1, column=0, columnspan=3, sticky=EW, pady=5)

        self.latitude = ttk.Label(self.data_frame, text='Latitud: ---', bootstyle=DARK, justify="center")
        self.latitude.grid(row=2, column=0, columnspan=2, sticky=W, pady=2)

        self.longitude = ttk.Label(self.data_frame, text='Longuitud: ---', bootstyle=DARK, justify="center")
        self.longitude.grid(row=2, column=2, sticky=EW, pady=2, padx=20)

        self.altitude = ttk.Label(self.data_frame, text='Distancia: ---', bootstyle=DARK, justify="center")
        self.altitude.grid(row=3, column=0, columnspan=2, sticky=W, pady=2)

        self.velocity = ttk.Label(self.data_frame, text='Velocidad: ---', bootstyle=DARK, justify="center")
        self.velocity.grid(row=3, column=2, sticky=EW, pady=2, padx=20)

        self.azimut = ttk.Label(self.data_frame, text='Azimut: ---', bootstyle=DARK, justify="center")
        self.azimut.grid(row=4, column=0, columnspan=2, sticky=W, pady=2)

        self.elevation = ttk.Label(self.data_frame, text='Elevación: ---', bootstyle=DARK, justify="center")
        self.elevation.grid(row=4, column=2, sticky=EW, pady=2, padx=20)

        self.controll_frame = ttk.Frame(root, width=300, height=200)
        self.controll_frame.grid(row=1, column=1, sticky="nsew")

        self.real_time = ttk.Button(self.controll_frame, text='Tiempo real', bootstyle=DARK, padding=5)
        self.real_time.grid(row=0, column=0, columnspan=3, sticky=NSEW, padx=5, pady=10)

        self.prediction = ttk.Button(self.controll_frame, text='Predicción', bootstyle=DARK, padding=5)
        self.prediction.grid(row=0, column=3, columnspan=3, sticky=NSEW, padx=5, pady=10)

        current_time = self.date.strftime("%m/%d/%Y  %H:%M:%S")

        self.prediction_date = ttk.Entry(self.controll_frame, bootstyle=DARK, textvariable=current_time)
        self.prediction_date.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=5, pady=10)

        self.prediction_date.delete(0, tk.END)
        self.prediction_date.insert(0, current_time)

        time_var = ttk.StringVar()
        time_var.set('1')
        self.time = ttk.Spinbox(self.controll_frame, bootstyle=DARK, from_=1, to=60, textvariable=time_var)
        self.time.grid(row=1, column=2, columnspan=2, sticky=NSEW, padx=5, pady=10)

        self.measure = ttk.Combobox(self.controll_frame, bootstyle=DARK, values=['Segundos', 'Minutos', 'Horas'])
        self.measure.current(0)
        self.measure.grid(row=1, column=4, columnspan=2, sticky=NSEW, padx=5, pady=10)

        self.stepper = ttk.Button(self.controll_frame, text='\u23ed Paso a paso', bootstyle=DARK, padding=5)
        self.stepper.grid(row=2, column=0, columnspan=3, sticky=NSEW, padx=5, pady=10)

        self.automatic = ttk.Button(self.controll_frame, text='\u23f5 Automático', bootstyle=DARK, padding=5, command=self.use_prediction)
        self.automatic.grid(row=2, column=3, columnspan=3, sticky=NSEW, padx=5, pady=10)

        # Inicializacion frame para el listado de checkbox(satelites)
        self.checkbox_frame = ttk.Frame(root, width=100, height=400, padding=[0, 10, 0, 10])
        self.checkbox_frame.grid(row=0, column=2, rowspan=2, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.checkbox_frame, orient="vertical", bootstyle="DARK, round")
        self.scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(self.checkbox_frame, yscrollcommand=self.scrollbar.set)
        checkbox_frame = ttk.Frame(canvas, style='TCheckbutton')
        self.scrollbar.config(command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

        # Función para configurar el scrolling del lienzo
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        checkbox_frame.bind("<Configure>", configure_scroll_region)

        # Variable de control para los checkboxes
        selected_checkbox = tk.IntVar(root, position)

        # Función para imprimir el valor del checkbox seleccionado
        def handle_checkbox():
            global selected_satellite
            index = selected_checkbox.get()
            satellite = sorted_satelliteList[index]
            selected_satellite =  satellite
            self.clear_trajectory()
            self.title_label.config(text = selected_satellite['satellite_name'])

        # Crear checkboxes con los datos proporcionados
        for index, data in enumerate(sorted_satelliteList):
            checkbox = ttk.Checkbutton(
                checkbox_frame,
                text=data["satellite_name"],
                variable=selected_checkbox,
                onvalue=index,
                command=handle_checkbox,
                bootstyle=DARK
            )
            checkbox.grid(row=index, column=0, sticky="w")

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
            lat, lon, dist, vel, elv, az = get_satellite_data(selected_satellite)

            self.map_ax.clear()
            self.map_ax.set_title((f"{et_city}, {abs(et_lat):.4f}° {'S' if et_lat < 0 else 'N'}, {abs(et_lon):.4f}° {'W' if et_lon < 0 else 'E'}"), loc="left", pad="10",fontdict = {'fontsize':10, 'color':'#373a3c'})
            self.map_ax.set_title(self.date.strftime("%Y-%m-%d  %H:%M:%S"), loc="right", pad="10",fontdict = {'fontsize':10, 'color':'#373a3c'})
            self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
            self.world_map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
            self.world_map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
            self.date = datetime.datetime.now()
            self.world_map.nightshade(utc_time)

            self.latitude.config(text=(f"{'Latitud: '}{abs(lat):.4f}° {'S' if lat < 0 else 'N'}"))
            self.longitude.config(text=(f"{'Longuitud: '}{abs(lon):.4f}° {'W' if lon < 0 else 'E'}"))
            self.altitude.config(text=(f"{'Distancia: '}{dist:.2f} km"))
            self.velocity.config(text=(f"{'Velocidad: '}{vel:.0f} km/h"))
            self.azimut.config(text=(f"{'Azimut: '}{az:.2f}°"))
            self.elevation.config(text=(f"{'Elevacion: '}{elv:.2f}°"))
            self.iss_positions.append((lat, lon))
            self.direction = ''

            if len(self.iss_positions) > 1:
                lats, lons = zip(*self.iss_positions)
                x, y = self.world_map(list(lons), list(lats))
                self.direction = '>' if lons[-1] > lons[-2] else '<'
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    self.world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-', linewidth=0.5)

            x, y = self.world_map(lon, lat)
            self.world_map.plot(x, y, 'wo', markersize=5)
            self.map_ax.text(x + 80000, y + 80000, selected_satellite['satellite_name'], color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')
            x, y = self.world_map(et_lon, et_lat)
            self.world_map.plot(x, y, 'w', markersize=5, marker='+')
            self.map_ax.text(x + 80000, y + 80000, et_city, color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')

        # Crear la animación
        self.ani = FuncAnimation(self.fig, update, frames=range(100), init_func=init, blit=False, interval=1000)

    def clear_trajectory(self):
        self.iss_positions.clear()

    def use_prediction(self):
        global selected_satellite
        prediction = self.rnn_instance.predict_orbit(selected_satellite)
