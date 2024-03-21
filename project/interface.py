import json
import ephem
import datetime
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from ttkbootstrap.constants import *
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AppInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("NeuralSatTrack")
        self.root.attributes('-zoomed', True)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        ttk.Style().configure("TCheckbutton", padding=10, font=('Helvetica', 10))

        global selected_satellite
        selected_satellite = {
            'satellite_name': 'FACSAT-2',
            'line_1': '1 56204U 23054AC  23334.73653880  .00010712  00000+0  42191-3 0  9996',
            'line_2': '2 56204  97.3879 227.5990 0013876 138.1327 222.0975 15.25695519 35559'
            }

        # Inicializacion frame para el lienzo del mapa
        self.map_frame = ttk.Frame(root, width=200, height=200)
        self.map_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Inicializacion del mapa base
        self.fig = plt.Figure(figsize=(15, 8), facecolor=(.133, .133, .133))
        self.map_ax = self.fig.add_subplot(1, 1, 1)

        # Configuración del mapa
        self.world_map = Basemap(projection='gall', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=self.map_ax)
        self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
        self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
        self.world_map.drawparallels(range(-90, 91, 30), textcolor='#F8F8F8', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
        self.world_map.drawmeridians(range(-180, 181, 30), textcolor='#F8F8F8', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
        self.date = datetime.datetime.now()
        self.world_map.nightshade(self.date)

        # Inicializacion frame para los controles
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.data_frame = ttk.Frame(root, width=200, height=200, padding=20)
        self.data_frame.grid(row=1, column=0 ,sticky="nsew")

        self.title_label = ttk.Label(self.data_frame, text=selected_satellite['satellite_name'], bootstyle=WARNING, justify="center")
        self.title_label.pack(side='top', pady=5, fill="x")

        self.separator = ttk.Separator(self.data_frame, bootstyle=WARNING)
        self.separator.pack(side='top', pady=5, fill="x")

        self.latitude = ttk.Label(self.data_frame, text='Latitud: ', bootstyle=WARNING, justify="center")
        self.latitude.pack(side='top', pady=5, fill="x")

        self.longitude = ttk.Label(self.data_frame, text='Longuitud: ', bootstyle=WARNING, justify="center")
        self.longitude.pack(side='top', pady=5, fill="x")
        
        self.controll_frame = ttk.Frame(root, width=200, height=200, bootstyle=DARK)
        self.controll_frame.grid(row=1, column=1, sticky="nsew")

        # Inicializacion frame para el listado de checkbox(satelites)
        self.checkbox_frame = ttk.Frame(root, width=100, height=400)
        self.checkbox_frame.grid(row=0, column=2, rowspan=2, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.checkbox_frame, orient="vertical", bootstyle="warning, round")
        self.scrollbar.pack(side="right", fill="y")

        # Crear un lienzo para los checkboxes
        canvas = tk.Canvas(self.checkbox_frame, yscrollcommand=self.scrollbar.set)
        checkbox_frame = ttk.Frame(canvas, style='TCheckbutton')
        self.scrollbar.config(command=canvas.yview)

        # Colocar el lienzo en el frame y el frame en el lienzo
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

        # Función para configurar el scrolling del lienzo
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        checkbox_frame.bind("<Configure>", configure_scroll_region)

        satelliteList = []
        with open('data/tle_data.json') as f:
            data = json.load(f)

        for satellite in data:
            satelliteList.append({
                "satellite_name": satellite["satellite_name"],
                "line_1": satellite["tle_1"],
                "line_2": satellite["tle_2"]
            })

        sorted_satelliteList = sorted(satelliteList, key=lambda x: x['satellite_name'])

        # Variable de control para los checkboxes
        selected_checkbox = tk.IntVar()

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
                bootstyle=WARNING
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
            self.map_ax.clear()
            self.map_ax.set_title(self.date.strftime("%m-%d-%Y  %H:%M:%S"), loc="right", pad="10",fontdict = {'fontsize':10, 'color':'#F8F8F8'})
            self.world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            self.world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            self.world_map.fillcontinents(color='#729951',lake_color='#2c5598')
            self.world_map.drawparallels(range(-90, 91, 30), textcolor='#F8F8F8', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
            self.world_map.drawmeridians(range(-180, 181, 30), textcolor='#F8F8F8', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
            self.date = datetime.datetime.now()
            self.world_map.nightshade(self.date)

            # Obtener la posición actual de la ISS
            lat, lon = self.get_sat_position()
            self.latitude.config(text=(f"{'Latitud: '}{abs(lat):.4f}° {'S' if lat < 0 else 'N'}"))
            self.longitude.config(text=(f"{'Longuitud: '}{abs(lon):.4f}° {'W' if lon < 0 else 'E'}"))
            self.iss_positions.append((lat, lon))
            self.direction = ''
            # Dibujar la trayectoria de la ISS
            if len(self.iss_positions) > 1:
                lats, lons = zip(*self.iss_positions)
                x, y = self.world_map(list(lons), list(lats))
                self.direction = '>' if lons[-1] > lons[-2] else '<'
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    self.world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-', linewidth=0.5)

            # Dibujar la posición actual de la ISS en el mapa
            x, y = self.world_map(lon, lat)
            self.world_map.plot(x, y, 'wo', markersize=8)

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

        satellite.compute()  # Calcular la posición del satélite
        lat = satellite.sublat / ephem.degree  # Latitud en grados
        lon = satellite.sublong / ephem.degree  # Longitud en grados
        position = (float(lat), float(lon))
        return position

    def clear_trajectory(self):
        self.iss_positions.clear()

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = AppInterface(root)
    root.mainloop()