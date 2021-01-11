import sys
import time
import json
import os.path
import requests
import pandas as pd
import numpy as np


def get_radius(area):
  coords = json.loads(area['geom'])['coordinates']
  ne = np.amax(coords, axis=1)[0][::-1]
  sw = np.amin(coords, axis=1)[0][::-1]
  # Reference: https://stackoverflow.com/a/33107765
  dist = abs(ne[0] - sw[0]) * 111 * 1000
  area['radius'] = dist / 2
  return area


def get_restaurant_data():
    API = "https://api.foursquare.com/v2/venues/explore"

    PARAMS = dict(
        client_id = "ZBXLABTCSSFRV1WBKBXCHF4PGZOT1PU4NZM0PDTV0W3YJYUD",
        client_secret = "TKFQRKGTUSBZ1MOWZICKXWOGEKW4PURJR3FD5FMGXOGJIK20",
        v = time.strftime("%Y%m%d"),
        # Venue params: https://developer.foursquare.com/docs/api-reference/venues/explore
        section = "food",
        radius = 1000,
        limit = 300
    )

    # Read the csv file containing information of regions in Vancouver and calculate the approximate radius of each region
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/local-area-boundary.csv"
    file_path = os.path.join(script_dir, relative_path)
    areas = pd.read_csv(file_path)
    areas = areas.apply(get_radius, axis=1)

    restaurants = pd.DataFrame()
    for i, area in areas.iterrows():
        # Set params
        PARAMS['ll'] = "{},{}".format(area['lat'], area['lng'])
        PARAMS['radius'] = area['radius']

        res = requests.get(url=API, params=PARAMS).json()
        data = res['response']['groups'][0]['items']

        # Format dataframes
        for i in range(len(data)):
            data[i] = data[i]['venue']
            data[i]['categories'] = data[i]['categories'][0]

        venues = pd.json_normalize(data)

        # Get columns
        cols = {
            'name': 'name', 
            'location.address': 'address',
            'categories.shortName': 'cuisine'
        }
        venues = venues[cols].rename(columns=cols)
        venues['region'] = area['name']
        print(venues)

        restaurants = restaurants.append(venues)

    # Save Foursquare restaurant data into a csv file
    script_dir = script_dir = os.path.dirname(__file__)
    relative_path = "../data/data_raw/Foursquare.csv"
    output_path = os.path.join(script_dir, relative_path)
    restaurants.to_csv(output_path, index=False)
