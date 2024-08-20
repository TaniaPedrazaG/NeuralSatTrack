import json
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from ttkbootstrap.constants import *
from datetime import datetime, timezone
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from satelliteCalculated import *
from predict import *

class Interface:
    def __init__(self, parent):
        root = parent
        root.title("NeuralSatTrack")
        root.attributes('-zoomed', True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        
        satellite_positions = []
        satelliteList = []
        global satellite_predictions
        global selected_satellite
        satellite_predictions = []

        ttk.Style().configure("TCheckbutton", padding=10, font=('Helvetica', 10))

        """ ---------- LIST_MODULE ----------"""

        checkbox_frame = ttk.Frame(root, width=100, height=400, padding=[0, 10, 0, 10])
        checkbox_frame.grid(row=0, column=2, rowspan=2, sticky="NSEW")

        scrollbar = ttk.Scrollbar(checkbox_frame, orient="vertical", bootstyle="DARK, round")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(checkbox_frame, yscrollcommand=scrollbar.set)
        checkbox_frame = ttk.Frame(canvas, style='TCheckbutton')
        scrollbar.config(command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        checkbox_frame.bind("<Configure>", configure_scroll_region)

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

        for i, element in enumerate(sorted_satelliteList):
            if element['satellite_name'] == 'ISS (ZARYA)':
                position = i
                break
            else:
                position = 0

        selected_checkbox = tk.IntVar(root, position)
        selected_satellite = sorted_satelliteList[position]

        get_in_range(selected_satellite)

        def clear_trajectory():
            satellite_positions.clear()

        def handle_checkbox():
            global selected_satellite
            index = selected_checkbox.get()
            satellite = sorted_satelliteList[index]
            selected_satellite = satellite
            get_in_range(satellite)
            clear_trajectory()

        for index, data in enumerate(sorted_satelliteList):
            checkbox = ttk.Checkbutton(
                checkbox_frame,
                text=data["satellite_name"],
                variable=selected_checkbox,
                onvalue=index,
                command=handle_checkbox,
                bootstyle="DARK"
            )
            checkbox.grid(row=index, column=0, sticky="w")
            
        """ ---------- INFO_MODULE ----------"""

        info_module = ttk.Frame(root, height=40)
        info_module.grid(row=1, column=0, columnspan=2, sticky="NSEW", padx=20, pady=10)

        et_lon, et_lat = observer_location()
        et_city = 'UPTC-GS'

        et_location = ttk.Label(info_module, text=(f"{et_city}, {abs(et_lat):.4f}° {'S' if et_lat < 0 else 'N'}, {abs(et_lon):.4f}° {'W' if et_lon < 0 else 'E'}"), font=('Helvetica', 10, 'bold'))
        et_location.pack(side="left")

        local_time = ttk.Label(info_module, text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"), font=('Helvetica', 10, 'bold'))
        local_time.pack(side="right")

        """ ---------- DATA_MODULE ----------"""

        data_module = ttk.Frame(root)
        data_module.grid(row=2, column=0, sticky="NSEW", padx=20, pady=10)

        sat_name = ttk.Label(data_module, text=selected_satellite['satellite_name'], font=('Helvetica', 12, 'bold'))
        sat_name.grid(row=0, column=0, sticky="EW", pady=2)

        separator = ttk.Separator(data_module, bootstyle="DARK")
        separator.grid(row=1, column=0, columnspan=5, sticky="NSEW", pady=5)

        sat_lon = ttk.Label(data_module, text='Longuitud:', font=('Helvetica', 11, 'bold'))
        sat_lon.grid(row=2, column=0, sticky="W", pady=2)
        sat_lon_value = ttk.Label(data_module, text='---')
        sat_lon_value.grid(row=2, column=1, sticky="EW", padx=5, pady=2)

        sat_lat = ttk.Label(data_module, text='Latitud:', font=('Helvetica', 11, 'bold'))
        sat_lat.grid(row=2, column=3, sticky="W", padx=20, pady=2)
        sat_lat_value = ttk.Label(data_module, text='---')
        sat_lat_value.grid(row=2, column=4, sticky="EW", padx=5, pady=2)

        dist = ttk.Label(data_module, text='Altura (km):', font=('Helvetica', 11, 'bold'))
        dist.grid(row=3, column=0, sticky="W", pady=2)
        dist_value = ttk.Label(data_module, text='---')
        dist_value.grid(row=3, column=1, sticky="EW", padx=5, pady=2)

        vel = ttk.Label(data_module, text='Velocidad (km/h):', font=('Helvetica', 11, 'bold'))
        vel.grid(row=3, column=3, sticky="W", padx=20, pady=2)
        vel_value = ttk.Label(data_module, text='---')
        vel_value.grid(row=3, column=4, sticky="EW", padx=5, pady=2)

        az = ttk.Label(data_module, text='Azimut:', font=('Helvetica', 11, 'bold'))
        az.grid(row=4, column=0, sticky="W", pady=2)
        az_value = ttk.Label(data_module, text='---')
        az_value.grid(row=4, column=1, sticky="EW", padx=5, pady=2)

        el = ttk.Label(data_module, text='Elevacion:', font=('Helvetica', 11, 'bold'))
        el.grid(row=4, column=3, sticky="W", padx=20, pady=2)
        el_value = ttk.Label(data_module, text='---')
        el_value.grid(row=4, column=4, sticky="EW", padx=5, pady=2)

        """ ---------- PREDICTIONS_MODULE ----------"""

        predictions_module = ttk.Frame(root)
        predictions_module.grid(row=2, column=1, sticky="NSEW", padx=20, pady=10)
        
        columns = ("Fecha y Hora", "Longitud", "Latitud", "Azimut", "Elevación")
        tree = tk.ttk.Treeview(predictions_module, columns=columns, show='headings', bootstyle="DARK")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=150, stretch=True)

        vsb = ttk.Scrollbar(predictions_module, orient="vertical", command=tree.yview, bootstyle="DARK, round")

        tree.configure(yscrollcommand=vsb.set)

        # Empacar el Treeview y las barras de desplazamiento
        tree.pack(side=tk.LEFT, fill='both', expand=True)
        vsb.pack(side=tk.RIGHT, fill='y')

        predictions_module.bind("<Configure>", configure_scroll_region)

        """ ---------- CONTROL_MODULE ----------"""

        control_module = ttk.Frame(root)
        control_module.grid(row=2, column=2, sticky="NSEW", padx=20, pady=10)

        real_time = ttk.Button(control_module, text='Tiempo real', bootstyle="DARK", padding=5, command=self.clean_prediction)
        real_time.grid(row=0, column=0, sticky="NSEW", padx=5, pady=10)

        current_time = datetime.now().strftime("%Y-%m-%d")

        prediction_date = ttk.Entry(control_module, bootstyle="DARK", textvariable=current_time)
        prediction_date.grid(row=1, column=0, sticky="NSEW", padx=5, pady=10)

        prediction_date.delete(0, tk.END)
        prediction_date.insert(0, current_time)

        prediction = ttk.Button(control_module, text='Predicción', bootstyle="DARK", padding=5, command=self.predict_orbit)
        prediction.grid(row=2, column=0, sticky="NSEW", padx=5, pady=10)

        """ ---------- MAP_MODULE ----------"""

        map_frame = ttk.Frame(root, width=400, height=200)
        map_frame.grid(row=0, column=0, columnspan=2, sticky="NSEW")
        
        fig = plt.Figure(figsize=(15, 8))
        map_ax = fig.add_subplot(1, 1, 1)
        
        world_map = Basemap(projection='gall', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=map_ax)
        world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
        world_map.fillcontinents(color='#729951',lake_color='#2c5598')
        world_map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
        world_map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
        world_map.nightshade(datetime.now(timezone.utc))
        
        self.canvas = FigureCanvasTkAgg(fig, master=map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        def init():
            return []
        
        def crosses_antimeridian(lon1, lon2):
            return abs(lon1 - lon2) > 180
        
        def update(frame):
            lat, lon, dist, vel, elv, az = get_satellite_data(selected_satellite)
            map_ax.clear()
            world_map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            world_map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            world_map.fillcontinents(color='#729951',lake_color='#2c5598')
            world_map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
            world_map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
            world_map.nightshade(datetime.now(timezone.utc))

            sat_lat_value.config(text=(f"{abs(lat):.4f}° {'S' if lat < 0 else 'N'}"))
            sat_lon_value.config(text=(f"{abs(lon):.4f}° {'W' if lon < 0 else 'E'}"))
            dist_value.config(text=(f"{dist:.2f}"))
            vel_value.config(text=(f"{vel:.0f}"))
            az_value.config(text=(f"{az:.2f}°"))
            el_value.config(text=(f"{elv:.2f}°"))
            local_time.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            satellite_positions.append((lat, lon))

            if len(satellite_positions) > 1:
                lats, lons = zip(*satellite_positions)
                x, y = world_map(list(lons), list(lats))
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-', linewidth=0.5)

            if len(satellite_predictions) > 1:
                time, lons, lats, azi = zip(*satellite_predictions)
                x, y = world_map(list(lons), list(lats))
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    world_map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'y-', linewidth=1)

                for row in satellite_predictions:
                    tree.insert("", tk.END, values=row)

            x, y = world_map(lon, lat)
            world_map.plot(x, y, 'wo', markersize=5)
            map_ax.text(x + 80000, y + 80000, selected_satellite['satellite_name'], color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')
            x, y = world_map(et_lon, et_lat)
            world_map.plot(x, y, 'w', markersize=5, marker='+')
            map_ax.text(x + 80000, y + 80000, et_city, color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')

        self.ani = FuncAnimation(fig, update, frames=range(100), init_func=init, blit=False, interval=1000)

    def use_prediction(self):
        return
    
    def clean_prediction(self):
        global satellite_predictions
        if len(satellite_predictions) > 0:
            satellite_predictions.clear()

    def predict_orbit(self):
        global selected_satellite
        global satellite_predictions
        positions = predict_values(selected_satellite)
        satellite_predictions = positions
