import time
import os.path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException


# Scrap restaurants data from Google Map and store them in a csv file
def get_restaurant_data(restaurant, chromedriver_path, debug_mode=False):
    keyword = restaurant['restaurant_name']
    num_pages = restaurant['num_pages_to_scrap']

    print("Scraping {} page(s) of restaurants with keyword '{}' from Google Map...".format(num_pages, keyword))

    # Open a file in the specified directory
    script_dir = os.path.dirname(__file__)
    relative_path = "../data/data_raw/" + keyword + ".csv"
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

    keyword = keyword.replace(" ", "%20")
    keyword = keyword.replace("&", "%26")
    keyword = keyword.replace("'", "%27")
    keyword = keyword.replace("+", "%2B")
    url = "https://www.google.com/maps/search/" + keyword
    driver.get(url)
    
    # Write the header into the file
    header = "name,address,rating,review_count"
    if debug_mode:
        print(header)
    f.write(header)
    
    for page in range(1, num_pages + 1):
        # Wait until the webpage is loaded
        time.sleep(5)

        # Go through each restaurant on the page
        try:
            restaurants = driver.find_elements_by_class_name("section-result-content")
        except NoSuchElementException:
            print("Failed to find any restaurants on page {}.".format(page))
            break

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
            rating = find_elem('span', 'cards-rating-score')
            review_count = find_elem('span', 'section-result-num-ratings')
                
            # Write the restaurant's data as a single csv line
            line = "\n" + name + "," + address + "," + rating + "," + review_count
            if debug_mode:
                print(line)
            f.write(line)
            
        # Go to the next page
        if page < num_pages:
            try:
                driver.find_element_by_xpath(".//button[@aria-label=' Next page ']").click()
            except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
                print("Failed to go to the next page.")
                break

    f.close()
    print("Scraping terminated. ({}/{})".format(page, num_pages))
