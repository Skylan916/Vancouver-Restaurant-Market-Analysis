# Vancouver Restaurant Market Analysis
Project by [Peter Lan](author) and [Jason Yeung](author)

Restaurants are constantly creating bucket loads of data, which, if used correctly, can prove to be a gold mine for a restaurant's success. The objective of this project is to analyze various Vancouver restaurant data to help determine the optimal location and the type of cuisine to specialize in for a new restaurant in Vancouver, BC. Considering the possibility of expanding the business into multiple locations in the future, we also examined chain restaurant data.

## Getting Started
Required Libraries:
- Python 3.7+
- Numpy
- Pandas
- Folium
- Geocoder
- Matplotlib
- Scikit Learn
- Scipy
- Seaborn
- Selenium
- Shapely
- Statsmodels

### How to run
After installing the above dependencies:

1. Gathering Data
```bash
# Requires chrome driver (https://chromedriver.chromium.org)
cd chain_restaurants/src
python data_collection.py

cd all_restaurants/src
python data_collection.py
```

2. Cleaning Data
```bash
# Requires a valid API key (https://developers.google.com/maps/documentation/geocoding/get-api-key)
cd chain_restaurants/src
python data_cleaning.py

cd all_restaurants/src
python data_cleaning.py
```

3. Analyzing Data
```bash
# Analyses are within 'data_analysis.ipynb'
```