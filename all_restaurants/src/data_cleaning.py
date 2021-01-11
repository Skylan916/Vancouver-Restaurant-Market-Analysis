import re
import glob
import os.path
import geocoder
import numpy as np
import pandas as pd
from shapely.geometry import Point
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

    # Iterate through each raw data file that contains information about multiple restaurants
    for i in range(file_count):
        path = paths[i]
        restaurants = pd.read_csv(path)

        # Drop rows with missing name, address, or cuisine type
        restaurants.dropna(subset=['name','address','cuisine'], inplace=True)

        # Drop unwanted entities
        ignore = [
            'Commercial real estate agency', 
            'Tour operator', 
            'Brewery', 
            'Airport',
            'Lounge',
            'Senior citizen center',
            'Marketing agency',
            'Shopping mall',
            'Beauty salon',
            'Car dealer',
            'Restaurant supply store',
            'Food processing equipment',
            'Liquor wholesaler',
            'Alcoholism treatment program',
            'Shipping and mailing service',
            'Cultural center',
            'Gutter Cleaning Service',
            'Massage therapist',
            'Distribution service',
            'Corporate office',
            'Pharmacy',
            'Wedding photographer',
            'Wholesale market',
            'Grocery store',
            'Asian grocery store',
            'Anglican church',
            'Tea house',
            '3-star hotel',
            '4-star hotel',
            '5-star hotel',
            'Restaurant',
        ]
        restaurants = restaurants[~(restaurants['cuisine'].isin(ignore))]

        # Consolidate similar restaurant types
        replace_cuisine = {
            'Indian takeout': 'Indian',
            'Modern Indian restaurant': 'Indian',
            'Italian grocery store': 'Italian',
            'Mexican goods store': 'Mexican',
            'Dim Sum': 'Chinese',
            'Hot Pot': 'Chinese',
            'Hong Kong style fast food restaurant': 'Chinese',
            'Peking Duck': 'Chinese',
            'Teppanyaki': 'Japanese',
            'Sushi': 'Japanese',
            'Sushi takeaway': 'Japanese',
            'Ramen': 'Japanese',
            'Korean BBQ': 'Korean',
            'Asian Fusion': 'Asian',
            'Pizza Delivery': 'Fast Food',
            'Pizza Takeout': 'Fast Food',
            'Tacos': 'Mexican',
            'Burritos': 'Mexican',
            'Deli / Bodega': 'Deli',
            'Cajun / Creole': 'Cajun',
            'Vegetarian / Vegan': 'Vegetarian',
            'Authentic Japanese': 'Japanese',
            'Bagel shop': 'Bagel',
        }
        restaurants['cuisine'] = restaurants['cuisine'].map(lambda c: (replace_cuisine[c] if (c in replace_cuisine) else c))

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
        restaurants.drop(columns=['price','rating','review_count','coordinates'], inplace=True, errors='ignore')
        restaurants.reset_index(drop=True, inplace=True)

        # Store the cleaned data
        file_name = re.search(r'data_raw/(.+)$', path).group(1)
        output_path = output_dir + file_name
        restaurants.to_csv(output_path, index=False)
        print("Cleaned '{}' ({}/{})".format(file_name, i+1, file_count))

        restaurant_list.append(restaurants)

    # Combine data into a single dataframe
    output_path = output_dir + "restaurants.csv"
    restaurants = pd.concat(restaurant_list, ignore_index=True)

    # Drop duplicate restaurants
    restaurants.drop_duplicates(subset=['address'], inplace=True)
    restaurants.drop_duplicates(subset=['lat','lng'], inplace=True)
    
    # Sort restaurants by their region
    restaurants.sort_values(by=['region','name'], inplace=True)
    
    restaurants.to_csv(output_path, index=False)
    print("Finished cleaning.")


if __name__ == '__main__':
    main()
