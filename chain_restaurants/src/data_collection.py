import os.path
import scraper
import pandas as pd


def main():
    # Path to the chrome driver (download at https://chromedriver.chromium.org/)
    chromedriver_path = "/Applications/chromedriver"
    debug_mode = False

    # Read the csv file containing a list of chain restaurants
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/chain_restaurant_list.csv"
    path = os.path.join(script_dir, relative_path)
    restaurant_list = pd.read_csv(path)

    # Sort the restaurants by name and overwrite the original csv file
    restaurant_list.sort_values(by=['restaurant_name'], inplace=True)
    restaurant_list.reset_index(drop=True, inplace=True)
    restaurant_list.to_csv(path, index=False)
    print(restaurant_list)

    # Scrap data from Google Map
    restaurant_list.apply(scraper.get_restaurant_data, axis=1, chromedriver_path=chromedriver_path, debug_mode=debug_mode)


if __name__ == '__main__':
    main()
