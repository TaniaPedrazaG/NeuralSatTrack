import os
import re
import json
import requests
from datetime import datetime
from threading import Thread
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

tle_urls = [
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=satnogs&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=engineering&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle'
]

class DownloadTLE:
    def __init__(self, root) -> None:
        self.root = root
        self.root.title("Confirmar")

        def close_window():
            self.root.after(3000, self.root.destroy)
    
        def download_tle():
            for url in tle_urls:
                response = requests.get(url)
                filename = os.path.basename(url)
                match = re.search(r'GROUP=(.*?)&FORMAT', filename)
                if match:
                    json_filename = match.group(1) + ".json"
                if response.status_code == 200:
                    tle_json = []
                    tmp_dict = {}
                    for i in response.text.split('\n'):
                        try:
                            if i.startswith('1'):
                                tmp_dict['tle_1'] = i.strip()
                            elif i.startswith('2'):
                                tmp_dict['tle_2'] = i.strip()
                            else:
                                tmp_dict['satellite_name'] = i.strip()
                            if "tle_1" in tmp_dict and "tle_2" in tmp_dict and "satellite_name" in tmp_dict:
                                tle_json.append(tmp_dict)
                                tmp_dict = {}
                        except Exception as e:
                            append_message(f"Error procesando los datos del satélite: {e}", 'danger')
                            return

                    try:
                        with open("data/" + json_filename, 'w') as f:
                            json.dump(tle_json, f, indent=3)
                            append_message(f"Archivo JSON '{json_filename}' creado correctamente.", 'success')
                    except Exception as e:
                        append_message(f"No se pudo crear el archivo: {json_filename}", 'danger')
                        return
                else:
                    append_message(f"No se pudo obtener el contenido de: {json_filename}", 'danger')
                    return

            close_window()

        def append_message(message, style):
            current_text = status_label.cget("text")
            if current_text:
                status_label.config(text=current_text + "\n" + message)
            else:
                status_label.config(text=message)
            # Apply style based on the `style` argument
            if style == 'success':
                status_label.config(bootstyle=SUCCESS)
            elif style == 'danger':
                status_label.config(bootstyle=DANGER)
            self.root.update()

        def start_download():
            download_thread = Thread(target=download_tle)
            download_thread.start()

        path_TLE = 'data/'
        timestamp_creation = os.path.getmtime(path_TLE)
        creation_date = datetime.fromtimestamp(timestamp_creation)

        confirm_frame = ttk.Frame(root, padding=20)
        confirm_frame.grid(row=0, column=0)

        paragraph = ttk.Label(confirm_frame, text="¿Desea ejecutar una actualización de los TLE?", anchor=CENTER, font=("Helvetica", 12))
        paragraph.grid(row=0, column=0, sticky=NSEW, columnspan=3, padx=10, pady=10)

        last_update = ttk.Label(confirm_frame, text=("Ultima actualización: {}".format(creation_date.date())), anchor=CENTER, font=("Helvetica", 10))
        last_update.grid(row=1, column=0, sticky=NSEW, columnspan=3, padx=10, pady=10)

        yes = ttk.Button(confirm_frame, text='Sí', bootstyle=SUCCESS, padding=[15, 10], command=start_download)
        yes.grid(row=2, column=0, sticky=NSEW)

        no = ttk.Button(confirm_frame, text='No', bootstyle=DANGER, padding=[15, 10], command=close_window)
        no.grid(row=2, column=2, sticky=NSEW)

        status_label = ttk.Label(confirm_frame, text="", anchor=W, font=("Helvetica", 10), wraplength=400)
        status_label.grid(row=3, column=0, sticky=NSEW, columnspan=3, padx=5, pady=5)
