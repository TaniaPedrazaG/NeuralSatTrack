import json
import requests

tle_urls = ['http://www.celestrak.com/NORAD/elements/active.txt',
            'http://celestrak.com/NORAD/elements/weather.txt',
            'http://celestrak.com/NORAD/elements/resource.txt',
            'https://www.celestrak.com/NORAD/elements/cubesat.txt',
            'http://celestrak.com/NORAD/elements/stations.txt',
            'https://www.celestrak.com/NORAD/elements/sarsat.txt',
            'https://www.celestrak.com/NORAD/elements/noaa.txt',
            'https://www.celestrak.com/NORAD/elements/amateur.txt',
            'https://www.celestrak.com/NORAD/elements/engineering.txt']


def download_tle():
    tle_json = []
    for url in tle_urls:
        request = requests.get(url)
        tmp_dict = {}
        for i in request.text.split('\n'):
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

    with open('data/tle_data.json', 'w') as f:
        json.dump(tle_json, f, indent=3)
        print('[+] Downloaded TLE data in tle_data.json')

if __name__ == '__main__':
    print('[+] Downloading TLE data...')
    download_tle()