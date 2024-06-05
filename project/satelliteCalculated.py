import json
import math
import time
import ephem
import datetime
from sgp4.api import jday
from sgp4.api import Satrec
from geopy.geocoders import Nominatim

def add_data(data, new_data):
    data.append(new_data)

def get_sat_position(selected_satellite, et_lat, et_lon):
    satellite_name = selected_satellite['satellite_name']
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']

    satellite = ephem.readtle(satellite_name, line1, line2)

    r, v = get_spherical_coordinates(selected_satellite)
    x, y, z = r
    r_mag = math.sqrt(x**2 + y**2 + z**2)

    vx, vy, vz = v
    vel = math.sqrt(vx**2 + vy**2 + vz**2)
    
    satellite.compute()
    lat = satellite.sublat / ephem.degree
    lon = satellite.sublong / ephem.degree
    alt = r_mag - 6378.155
    position = (float(lat), float(lon), float(alt), float(vel))
    azimut = calculate_azimut(et_lat, et_lon, lat, lon)

    new_data = {
        'lon': float(lon),
        'lat': float(lat),
        'alt': float(alt),
        'azimut': float(azimut),
        'timestamp': time.time(),
    }

    file_name = 'data/train_' + satellite_name + '.json'
    current_data = read_json_data(file_name)
    add_data(current_data, new_data)
    write_json_data(file_name, current_data)

    return position

def get_spherical_coordinates(selected_satellite):
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']

    satellite = Satrec.twoline2rv(line1, line2)
    now = datetime.datetime.now()

    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second
    jd, fr = jday(year, month, day, hour, minute, second)
    e, r, v = satellite.sgp4(jd, fr)
    
    return r, v

def get_elevation(sat_lon):
    HCS = 42164.2
    R = 6378.155
    et_lon, et_lat = observer_location()
    lonSAT = math.radians(abs(sat_lon))
    lonET = math.radians(abs(et_lon))
    latET = math.radians(abs(et_lat))

    alfa = math.acos((math.cos(math.radians(latET))) * (math.cos(math.radians(lonSAT - lonET))))
    numerator = HCS - (R * math.cos(alfa))
    denominator = R * math.sin(alfa)
    elevation_angle = math.degrees(math.atan(numerator / denominator))
    elevation = elevation_angle - alfa

    return elevation

def get_orbital_trace(selected_satellite):
    distance = 6371.0 + 400
    area_segmento = 2 * math.pi * 6371.0 * distance

    return area_segmento

def observer_location():
    # geolocator = Nominatim(user_agent="MyApp")
    # loc = geolocator.geocode('Sogamoso')
    
    return {-72.7992, 5.1578}

def read_json_data(name_file):
    try:
        with open(name_file, 'r') as archivo:
            datos = json.load(archivo)
    except FileNotFoundError:
        datos = []

    return datos

def write_json_data(name_file, data):
    with open(name_file, 'w') as archivo:
        json.dump(data, archivo, indent=3)

def calculate_azimut(lat_et, lon_et, lat_sat, lon_sat):
    d_v = lat_sat - lat_et
    d_h = lon_sat - lon_et
    O_ = math.atan(math.radians(abs(d_v)) / math.radians(abs(d_h)))
    O_ = math.degrees(O_)

    if d_v > 0 and d_h < 0:
        O_ = 180 - O_
    if d_v < 0 and d_h < 0:
        O_ += 180
    if d_v < 0 and d_h > 0:
        O_ = 360 - O_
    if  d_v > 0 and d_h > 0:
        O_ = 90 - O_
    
    return O_

def calculate_excentric_anomaly(e, M, iteration):
    if iteration < 100:
        ++iteration
        return M - e * math.sin(calculate_excentric_anomaly(e, M, iteration))
    else:
        return M

def calculate_true_anomaly(e, E):
    O_ = math.degrees(math.sin((math.cos(E) - e) / (1 - e * math.cos(E))))
    E = math.degrees(E)
    if E >= 0 and E < 180:
        O_ = -1 * O_ + 90
    if E >= 180 and E <= 360:
        O_ += 270
    return O_

def calculate_ratio(e, O_, a):
    return a * (1 - math.pow(e, 2)) / (1 + e * math.cos(math.radians(O_)))

def calculate_altitude_ecuator(Y, i):
    return i * math.sin(math.radians(Y))

def calculate_BEAM_ratio(h):
    O_ = math.asin(6400 / h)
    return 90 - math.degrees(O_)

def geographic_to_cartesian(lat, lon, alt):
    R = 6378.155
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    x = (R + alt) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (R + alt) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (R + alt) * math.sin(lat_rad)
    
    return x, y, z

""" def calculate_satellite_distance(lat_et, lon_et, lat_sat, lon_sat):
    tmp1 = math.pow(lat_sat - lat_et, 2)
    tmp2 = math.pow(lon_sat - lon_et, 2)
    d = math.pow(tmp1 + tmp2, 0.5)
    if d > 180:
        d = 360 - d % 180
    return d """