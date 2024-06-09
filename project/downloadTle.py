import re
import os
import json
import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

tle_urls = [
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=satnogs&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=engineering&FORMAT=tle',
    'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
]

class DownloadTLE:
    def __init__(self, root) -> None:
        self.root = root
        self.root.title("Confirmar")

        def close_window():
            self.root.destroy()
    
        def download_tle():
            tle_json = []
            for url in tle_urls:
                response = requests.get(url)
                filename = os.path.basename(url)
                match = re.search(r'GROUP=(.*?)&FORMAT', filename)
                if match:
                    json_filename = match.group(1) + ".json"
                if response.status_code == 200:
                    tmp_dict = {}
                    for i in response.text.split('\n'):
                        try:
                            if i[0] == '1':
                                tmp_dict['tle_1'] = i.strip()
                            elif i[0] == '2':
                                tmp_dict['tle_2'] = i.strip()
                            else:
                                tmp_dict['satellite_name'] = i.strip()
                            if "tle_1" in tmp_dict and "tle_2" in tmp_dict and "satellite_name" in tmp_dict:
                                tle_json.append(tmp_dict)
                                tmp_dict = {}
                            else:
                                pass
                        except:
                            pass
                    with open("data/" + json_filename, 'w') as f:
                        json.dump(tle_json, f, indent=3)
                        print(f"Archivo JSON '{json_filename}' creado correctamente.")
                else:
                    print(f"No se pudo obtener el contenido de: {json_filename}")
            close_window()

        confirm_frame = ttk.Frame(root, padding=20)
        confirm_frame.grid(row=0, column=0)

        paragraph = ttk.Label(confirm_frame, text="¿Desea ejecutar una actualización de los TLE?")
        paragraph.grid(row=0, column=0, sticky=NSEW, columnspan=3, padx=10, pady=10)

        yes = ttk.Button(confirm_frame, text='Sí', bootstyle=SUCCESS, padding=[15, 10], command=download_tle)
        yes.grid(row=1, column=0, sticky=NSEW)

        no = ttk.Button(confirm_frame, text='No', bootstyle=DANGER, padding=[15, 10], command=close_window)
        no.grid(row=1, column=2, sticky=NSEW)
