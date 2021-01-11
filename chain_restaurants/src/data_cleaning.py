import re
import glob
import os.path
import geocoder
import numpy as np
import pandas as pd
from shapely.geometry import Point
from difflib import SequenceMatcher
from shapely.geometry.polygon import Polygon


# Convert the given address to geolocation
# Return (lat,lng) if successful, return nan otherwise
def forward_geocode(address):
    address = address + ", BC, Canada"
    key = "PlaceYourKeyHere"
    g = geocoder.google(address, key=key)
    if (g.ok):
        return g.latlng
    return np.nan


# Return a dataframe that contains various information about regions within Vancouver
def get_regions():
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/local-area-boundary.json"
    path = os.path.join(script_dir, relative_path)
    df = pd.read_json(path)
    regions = pd.json_normalize(df['fields'])
    regions.rename(columns={'geom.coordinates':'coordinates'}, inplace = True) 
    regions.drop(columns=['mapid','geo_point_2d','geom.type'], inplace=True)

    # Convert the coordinates column into the desired format
    # e.g. [[[lng,lat],...,[lng,lat]]] to [[lat,lng],...,[lat,lng]]
    def swap_coordinates(coordinates):
        coordinates = coordinates[0]
        lat_list = list(list(zip(*coordinates))[1])
        lng_list = list(list(zip(*coordinates))[0])
        return np.column_stack((lat_list,lng_list))
    regions['coordinates'] = regions['coordinates'].apply(swap_coordinates)
    return regions


# Return a list of restaurants raw data file path
def get_raw_data_paths():
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/data_raw"
    path = os.path.join(script_dir, relative_path)
    paths = glob.glob(path + "/*.csv")
    return paths


# Return True if s1 contains s2 or s1 and s2 are similar strings
# Return False otherwise
def is_close_match(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    if s2 in s1:
        return True
    ratio = SequenceMatcher(a=s1,b=s2).ratio()
    if ratio > 0.5:
        return True
    return False


# Return the path of the output directory
def get_output_dir():
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/data_clean/"
    path = os.path.join(script_dir, relative_path)
    return path


def main():
    restaurant_list = []
    regions = get_regions()
    paths = get_raw_data_paths()
    file_count = len(paths)
    output_dir = get_output_dir()

    print("Cleaning {} csv files...".format(file_count))
    print("Output directory: {}".format(output_dir))

    # Iterate through each raw data file that contains information about multiple chain restaurants
    for i in range(file_count):
        path = paths[i]
        restaurants = pd.read_csv(path)

        # Drop rows with missing value
        restaurants.dropna(inplace=True)

        # Filter out irrelevant resturants
        restaurant_name = re.search(r'data_raw/(.+).csv$', path).group(1)
        restaurants['is_close_match'] = restaurants['name'].apply(is_close_match, args=(restaurant_name,))
        restaurants = restaurants[restaurants['is_close_match']==True]

        # Filter out unrealistic rating and review count
        restaurants['rating'] = pd.to_numeric(restaurants['rating'], errors='coerce')
        restaurants['review_count'] = pd.to_numeric(restaurants['review_count'], errors='coerce')
        restaurants.dropna(subset=['rating','review_count'], inplace=True)
        restaurants = restaurants[(restaurants['rating']>=0) & (restaurants['rating']<=5)]
        restaurants = restaurants[restaurants['review_count']>=0]

        # Get lat and lng for each restaurant location and drop rows with an invalid address
        restaurants['coordinates'] = restaurants['address'].apply(forward_geocode)
        restaurants.dropna(subset=['coordinates'], inplace=True)
        restaurants[['lat','lng']] = pd.DataFrame(restaurants['coordinates'].tolist(), index=restaurants.index) 

        # Determine the region of each restaurant and filter out restaurants that are not in Vancouver
        def determine_region(restaurant):
            x = restaurant['lat']
            y = restaurant['lng']
            point = Point(x,y)
            for index, row in regions.iterrows():
                polygon = Polygon(row['coordinates']) 
                if (point.within(polygon)):
                    return row['name']
            return 'Other'
        restaurants['region'] = restaurants.apply(determine_region, axis=1)
        restaurants = restaurants[restaurants['region']!='Other']

        # Drop redundant columns and reset index
        restaurants.drop(columns=['address','is_close_match','coordinates'], inplace=True)
        restaurants.reset_index(drop=True, inplace=True)

        # Store the cleaned data
        output_path = output_dir + restaurant_name + ".csv"
        restaurants.to_csv(output_path, index=False)
        print("Cleaned '{}.csv' ({}/{})".format(restaurant_name, i+1, file_count))

        restaurant_list.append(restaurants)

    # Combine, sort and store all chain restaurants data into a single csv file
    output_path = output_dir + "restaurants.csv"
    restaurants = pd.concat(restaurant_list, ignore_index=True)
    restaurants.sort_values(by=['name'], inplace=True)
    restaurants.to_csv(output_path, index=False)

    print("Finished cleaning.")


if __name__ == '__main__':
    main()
