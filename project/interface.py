import os
import json
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from ttkbootstrap.constants import *
from datetime import datetime, timezone
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from RNN import RNNPrediction
from satelliteCalculated import *

class Interface:
    def __init__(self, parent):
        root = parent
        root.title("NeuralSatTrack")
        root.attributes('-zoomed', True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        iss_positions = []
        satelliteList = []
        global selected_satellite
        rnn_instance = RNNPrediction()

        ttk.Style().configure("TCheckbutton", padding=10, font=('Helvetica', 10))

        """ ---------- LIST_MODULE ----------"""

        list_module = ttk.Frame(root, width=50)
        list_module.grid(row=0, column=2, rowspan=3, sticky=NSEW, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_module, orient="vertical", bootstyle="DARK, round")
        scrollbar.pack(side=RIGHT, fill=Y)

        canvas = tk.Canvas(list_module, yscrollcommand=scrollbar.set)
        list_module = ttk.Frame(canvas, style='TCheckbutton')
        scrollbar.config(command=canvas.yview)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        canvas.create_window((0, 0), window=list_module, anchor=NW)

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        list_module.bind("<Configure>", configure_scroll_region)

        for filename in os.listdir('data'):
            if filename.endswith('.json'):
                filepath = os.path.join('data', filename)
                try:
                    with open(filepath, 'r') as file:
                        data = json.load(file)

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
                    
                    selected_checkbox = tk.IntVar(root, position)
                    selected_satellite = sorted_satelliteList[position]

                    def clear_trajectory():
                        iss_positions.clear()

                    def handle_checkbox():
                        global selected_satellite
                        index = selected_checkbox.get()
                        satellite = sorted_satelliteList[index]
                        selected_satellite =  satellite
                        clear_trajectory()

                    for index, data in enumerate(sorted_satelliteList):
                        checkbox = ttk.Checkbutton(
                            list_module,
                            text=data["satellite_name"],
                            variable=selected_checkbox,
                            onvalue=index,
                            command=handle_checkbox,
                            bootstyle=DARK
                        )
                        checkbox.grid(row=index, column=0, sticky="w")
                except Exception as e:
                    print(f"Error al leer {filename}: {e}")

        """ ---------- MAP_MODULE ----------"""

        map_module = ttk.Frame(root)
        map_module.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        fig = plt.Figure()

        map_ax = fig.add_subplot(111)

        map = Basemap(projection='gall',llcrnrlat=-90,urcrnrlat=90,llcrnrlon=-180,urcrnrlon=180,resolution='c', ax=map_ax)
        map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
        map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
        map.fillcontinents(color='#729951',lake_color='#2c5598')
        map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
        map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
        map.nightshade(datetime.datetime.now(timezone.utc))

        map_canvas = FigureCanvasTkAgg(fig, master=map_module)
        map_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        def init_animation():
            return []
        
        def crosses_antimeridian(lon1, lon2):
            return abs(lon1 - lon2) > 180

        def update(frame):
            lat, lon, dist, vel, elv, az = get_satellite_data(selected_satellite)
            iss_positions.append((lat, lon))

            sat_lon_value.config(text=(f"{abs(lon):.4f}° {'W' if lon < 0 else 'E'}"))
            sat_lat_value.config(text=(f"{abs(lat):.4f}° {'S' if lat < 0 else 'N'}"))
            dist_value.config(text=(f"{dist:.2f}"))
            vel_value.config(text=(f"{vel:.0f}"))
            az_value.config(text=(f"{az:.2f}°"))
            el_value.config(text=(f"{elv:.2f}°"))

            map_ax.clear()
            map.drawcoastlines(linewidth=0.5, linestyle='solid', color='k', antialiased=1, ax=None, zorder=None)
            map.drawmapboundary(color='k', linewidth=0.5, fill_color='#2c5598', zorder=None, ax=None)
            map.fillcontinents(color='#729951',lake_color='#2c5598')
            map.drawparallels(range(-90, 91, 30), textcolor='#373a3c', labels=[0, 1, 0, 0], linewidth=0.5, fontsize=6)
            map.drawmeridians(range(-180, 181, 30), textcolor='#373a3c', labels=[0, 0, 0, 1], linewidth=0.5, fontsize=6)
            map.nightshade(datetime.datetime.now(timezone.utc))

            if len(iss_positions) > 1:
                lats, lons = zip(*iss_positions)
                x, y = map(list(lons), list(lats))
                for i in range(len(x)-1):
                    if crosses_antimeridian(lons[i], lons[i+1]):
                        continue
                    map.plot([x[i], x[i+1]], [y[i], y[i+1]], 'w-', linewidth=0.5)

            x, y = map(lon, lat)
            map.plot(x, y, 'wo', markersize=5)
            map_ax.text(x + 80000, y + 80000, selected_satellite['satellite_name'], color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')
            x, y = map(et_lon, et_lat)
            map.plot(x, y, 'w', markersize=5, marker='+')
            map_ax.text(x + 80000, y + 80000, et_city, color='white', fontsize=8, fontweight='semibold', ha='left', va='bottom')

        anim = FuncAnimation(fig, update, frames=range(100), init_func=init_animation, blit=False, interval=1000)
        plt.show()

        """ ---------- INFO_MODULE ----------"""

        info_module = ttk.Frame(root, height=40)
        info_module.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=20, pady=10)

        et_lon, et_lat = observer_location()
        et_city = 'Sogamoso'

        et_location = ttk.Label(info_module, text=(f"{et_city}, {abs(et_lat):.4f}° {'S' if et_lat < 0 else 'N'}, {abs(et_lon):.4f}° {'W' if et_lon < 0 else 'E'}"), font=('Helvetica', 10, 'bold'))
        et_location.pack(side=LEFT)

        local_time = ttk.Label(info_module, text=datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S"), font=('Helvetica', 10, 'bold'))
        local_time.pack(side=RIGHT)

        """ ---------- DATA_MODULE ----------"""

        data_module = ttk.Frame(root)
        data_module.grid(row=2, column=0, sticky=NSEW, padx=20, pady=10)

        sat_name = ttk.Label(data_module, text=selected_satellite['satellite_name'], font=('Helvetica', 12, 'bold'))
        sat_name.grid(row=0, column=0, sticky=W, pady=2)

        sat_lon = ttk.Label(data_module, text='Longuitud:', font=('Helvetica', 11, 'bold'))
        sat_lon.grid(row=1, column=0, sticky=W, pady=2)
        sat_lon_value = ttk.Label(data_module, text='---')
        sat_lon_value.grid(row=1, column=1, sticky=EW, padx=5, pady=2)

        sat_lat = ttk.Label(data_module, text='Latitud:', font=('Helvetica', 11, 'bold'))
        sat_lat.grid(row=1, column=3, sticky=W, padx=20, pady=2)
        sat_lat_value = ttk.Label(data_module, text='---')
        sat_lat_value.grid(row=1, column=4, sticky=EW, padx=5, pady=2)

        dist = ttk.Label(data_module, text='Altura (km):', font=('Helvetica', 11, 'bold'))
        dist.grid(row=2, column=0, sticky=W, pady=2)
        dist_value = ttk.Label(data_module, text='---')
        dist_value.grid(row=2, column=1, sticky=EW, padx=5, pady=2)

        vel = ttk.Label(data_module, text='Velocidad (km/h):', font=('Helvetica', 11, 'bold'))
        vel.grid(row=2, column=3, sticky=W, padx=20, pady=2)
        vel_value = ttk.Label(data_module, text='---')
        vel_value.grid(row=2, column=4, sticky=EW, padx=5, pady=2)

        az = ttk.Label(data_module, text='Azimut:', font=('Helvetica', 11, 'bold'))
        az.grid(row=3, column=0, sticky=W, pady=2)
        az_value = ttk.Label(data_module, text='---')
        az_value.grid(row=3, column=1, sticky=EW, padx=5, pady=2)

        el = ttk.Label(data_module, text='Elevacion:', font=('Helvetica', 11, 'bold'))
        el.grid(row=3, column=3, sticky=W, padx=20, pady=2)
        el_value = ttk.Label(data_module, text='---')
        el_value.grid(row=3, column=4, sticky=EW, padx=5, pady=2)

        """ ---------- CONTROL_MODULE ----------"""

        control_module = ttk.Frame(root)
        control_module.grid(row=2, column=1, sticky=NSEW, padx=20, pady=10)
        control_module.columnconfigure(0, weight=1)
        control_module.columnconfigure(1, weight=1)
        control_module.columnconfigure(2, weight=1)
        control_module.columnconfigure(3, weight=1)
        control_module.columnconfigure(4, weight=1)

        real_time = ttk.Button(control_module, text='Tiempo real', bootstyle=DARK, padding=5)
        real_time.grid(row=0, column=0, columnspan=3, sticky=NSEW, padx=5, pady=10)

        prediction = ttk.Button(control_module, text='Predicción', bootstyle=DARK, padding=5)
        prediction.grid(row=0, column=3, columnspan=3, sticky=NSEW, padx=5, pady=10)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        prediction_date = ttk.Entry(control_module, bootstyle=DARK, textvariable=current_time)
        prediction_date.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=5, pady=10)

        prediction_date.delete(0, tk.END)
        prediction_date.insert(0, current_time)

        time_var = ttk.StringVar()
        time_var.set(1)
        time = ttk.Spinbox(control_module, bootstyle=DARK, from_=1, to=60, textvariable=time_var)
        time.grid(row=1, column=2, columnspan=2, sticky=NSEW, padx=5, pady=10)

        measure = ttk.Combobox(control_module, bootstyle=DARK, values=['Segundos', 'Minutos', 'Horas'])
        measure.current(0)
        measure.grid(row=1, column=4, columnspan=2, sticky=NSEW, padx=5, pady=10)

        stepper = ttk.Button(control_module, text='\u23ed Paso a paso', bootstyle=DARK, padding=5)
        stepper.grid(row=2, column=0, columnspan=3, sticky=NSEW, padx=5, pady=10)

        def use_prediction():
            global selected_satellite
            prediction = rnn_instance.predict_orbit(selected_satellite)

        automatic = ttk.Button(control_module, text='\u23f5 Automático', bootstyle=DARK, padding=5, command=use_prediction)
        automatic.grid(row=2, column=3, columnspan=3, sticky=NSEW, padx=5, pady=10)

