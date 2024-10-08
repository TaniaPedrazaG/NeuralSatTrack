from datetime import datetime, timedelta
import csv
import json
import math
import os
from sgp4.api import jday
from sgp4.api import Satrec
from skyfield.api import EarthSatellite, load, wgs84, Topos

def add_data(data, new_data):
    data.append(new_data)

def observer_location():
    # geolocator = Nominatim(user_agent="MyApp")
    # loc = geolocator.geocode('Sogamoso')
    return -72.94039833237998, 5.704908307157419

def calc_distance_sat_et(r):
    x, y, z = r
    r_mag = math.sqrt(x**2 + y**2 + z**2)
    return r_mag

def calc_distance_sat_cent(alt_sat):
    R = 6378.155
    return R + alt_sat

def get_spherical_coordinates(selected_satellite):
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']

    satellite = Satrec.twoline2rv(line1, line2)
    now = datetime.now()

    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second
    jd, fr = jday(year, month, day, hour, minute, second)
    e, r, v = satellite.sgp4(jd, fr)
    return r, v

def calc_azimut(lonSAT):
    lonET, latET = observer_location()
    A = math.atan(math.tan(math.radians(lonSAT - lonET)) / math.sin(math.radians(latET)))
    if latET > 0:
        if lonSAT < lonET:
            az = 180 + math.degrees(A)
        if lonSAT > lonET:
            az = 180 - math.degrees(A)
    if latET < 0:
        if lonSAT < lonET:
            az = 360 - math.degrees(A)
        if lonSAT > lonET:
            az = math.degrees(A)
    return az

def calc_elevation(date_time_str, selected_satellite):
    satellite_name = selected_satellite['satellite_name']
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']
    
    satellite = EarthSatellite(line1, line2, satellite_name, load.timescale())
    
    observer_location = Topos('5.704908307157419 N', '72.94039833237998 W')
    
    ts = load.timescale()
    
    observation_time = date_time_str
    t = ts.utc(observation_time.year, observation_time.month, observation_time.day,
            observation_time.hour, observation_time.minute, observation_time.second)
    
    difference = satellite - observer_location
    topocentric = difference.at(t)
    
    alt, az, distance = topocentric.altaz()
    return alt.degrees

def get_satellite_data(selected_satellite):
    G = 6.67430e-11
    M = 5.972e24 
    ts = load.timescale()
    satellite_name = selected_satellite['satellite_name']
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']
    satellite = EarthSatellite(line1, line2, satellite_name, ts)

    lonET, latET = observer_location()

    bluffton = wgs84.latlon(latET, lonET)
    t0 = ts.utc(2024, 6, 15)
    t1 = ts.utc(2024, 6, 16)
    t, events = satellite.find_events(bluffton, t0, t1, altitude_degrees=30.0)
    event_names = 'rise above 30°', 'culminate', 'set below 30°'
    for ti, event in zip(t, events):
        name = event_names[event]

    t = ts.now()

    geocentric = satellite.at(t)

    lat, lon = wgs84.latlon_of(geocentric)

    difference = satellite - bluffton

    topocentric = difference.at(t)

    alt, az, distance = topocentric.altaz()

    ra, dec, distance = topocentric.radec(epoch='date')

    r, v = get_spherical_coordinates(selected_satellite)
    r_dist= calc_distance_sat_et(r)
    distance = r_dist - 6378.155

    r_total = calc_distance_sat_cent(distance)
    vel = math.sqrt(G * M / r_total)

    azimut = calc_azimut(lon.degrees)
    return lat.degrees, lon.degrees, distance, vel, alt.degrees, azimut

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

def verify_update(selected_satellite, predict_date):
    sat_name = selected_satellite['satellite_name']
    path_TLE = 'data/historic/' + sat_name +'.csv'
    if not os.path.exists(path_TLE):
        return
    timestamp_creation = os.path.getmtime(path_TLE)
    creation_date = datetime.fromtimestamp(timestamp_creation)
    return creation_date.date() == predict_date

def get_in_range(selected_satellite, predict_date):
    if verify_update(selected_satellite, predict_date):
        return
    
    formatted_date = datetime.strptime(predict_date, "%d/%m/%y")

    day = formatted_date.day
    month = formatted_date.month
    year = formatted_date.year

    if year < 100:
        year += 2000
    
    date_next_day = formatted_date + timedelta(days=1)
    next_day = date_next_day.day

    ts = load.timescale()
    satellite_name = selected_satellite['satellite_name']
    line1 = selected_satellite['line_1']
    line2 = selected_satellite['line_2']
    satellite = EarthSatellite(line1, line2, satellite_name, ts)
    
    output_file = 'data/historic/' + satellite_name + '.csv'
    
    start_time = datetime(year, month, day, 5, 0, 0)
    end_time = datetime(year, month, next_day, 5, 0, 0)
    delta = timedelta(seconds=30)
    
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'latitude', 'longitude'])
        
        current_time = start_time
        
        while current_time <= end_time:
            ts = load.timescale()
            t = ts.utc(current_time.year, current_time.month, current_time.day,
                    current_time.hour, current_time.minute, current_time.second)
            
            geocentric = satellite.at(t)
            subpoint = geocentric.subpoint()
            latitude = subpoint.latitude.degrees
            longitude = subpoint.longitude.degrees

            adjusted_time = current_time - timedelta(hours=5)
            
            writer.writerow([adjusted_time, latitude, longitude])
            
            current_time += delta
