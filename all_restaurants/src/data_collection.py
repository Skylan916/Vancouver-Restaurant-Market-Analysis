import os.path
import scraper
import foursquare
import pandas as pd


def main():
    # Path to the chrome driver (download at https://chromedriver.chromium.org/)
    chromedriver_path = "/Applications/chromedriver"
    debug_mode = False

    # Read the csv file containing information of regions in Vancouver
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/local-area-boundary.csv"
    path = os.path.join(script_dir, relative_path)
    regions = pd.read_csv(path)
    print(regions['name'])

    # Scrap data from Google Map
    regions.apply(scraper.get_restaurant_data, axis=1, chromedriver_path=chromedriver_path, debug_mode=debug_mode)

    # Fetch data from Foursquare
    foursquare.get_restaurant_data()


if __name__ == '__main__':
    main()
