import time
import os.path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException


# Scrap restaurants data from Google Map and store them in a csv file
def get_restaurant_data(region, chromedriver_path, debug_mode=False):
    region = region['name']

    print("Scraping data of restaurants located in {} from Google Map...".format(region))

    # Open a file in the specified directory
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/data_raw/" + region + ".csv"
    file_path = os.path.join(script_dir, relative_path)
    if debug_mode:
        print("file path:", file_path)
    f = open(file_path, "w")

    # Initialize the webdriver
    options = webdriver.ChromeOptions()

    if (not debug_mode):
        # Scrape without a new Chrome window every time
        options.add_argument("headless")
    
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
    driver.set_window_size(1480, 1080)

    url = "https://www.google.com/maps/search/Restaurants+in+{},Vancouver,BC".format(region)
    driver.get(url)
    
    # Write the header into the file
    header = "name,address,cuisine,price,rating,review_count"
    if debug_mode:
        print(header)
    f.write(header)
    
    num_pages = 0
    while (num_pages < 100):
        # Wait until the webpage is loaded
        time.sleep(5)

        # Go through each restaurant on the page
        try:
            restaurants = driver.find_elements_by_class_name("section-result-content")
        except NoSuchElementException:
            break

        num_pages += 1
        for restaurant in restaurants:
            def find_elem(html_element, html_class):
                try: 
                    result = restaurant.find_element_by_xpath(".//{}[@class='{}']".format(html_element, html_class)).text
                    result = result.replace(',', '')
                    result = result.strip("()")
                except NoSuchElementException:
                    result = ''
                return result

            name = find_elem('h3', 'section-result-title')
            address = find_elem('span', 'section-result-location')
            cuisine = find_elem('span', 'section-result-details')
            price = find_elem('span', 'section-result-cost')
            rating = find_elem('span', 'cards-rating-score')
            review_count = find_elem('span', 'section-result-num-ratings')
                
            # Write the restaurant's data as a single csv line
            line = "\n" + name + "," + address + "," + cuisine + "," + price + "," + rating + "," + review_count
            if debug_mode:
                print(line)
            f.write(line)
            
        # Go to the next page
        try:
            driver.find_element_by_xpath(".//button[@aria-label=' Next page ']").click()
        except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
            break

    f.close()
    print("Scraped restaurant data from {} pages. Scraping terminated.".format(num_pages))
