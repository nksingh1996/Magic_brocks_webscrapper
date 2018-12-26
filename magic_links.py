from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions as seleniumExceptions
import time
from bs4 import BeautifulSoup
import logging
import sys

"""
using sys takes input form command line and command is -
python3 filename.py suggested_regions_file threshold(numner
 of min links after which they will be written to output_file) output_file
"""

filehandler_except = logging.FileHandler('exceptions.log')
filehandler_info = logging.FileHandler('info.log')

logging.basicConfig(filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

logger_exc = logging.getLogger('exceptions')
logger_exc.addHandler(filehandler_except)

logger_info = logging.getLogger('info')
logger_info.addHandler(filehandler_info)


def get_driver(headless=True):
    """
    returns firefox webdriver(geckodriver), headless means browser will not launch
    """
    options = Options()
    options.set_headless(headless=headless)
    driver = webdriver.Firefox(firefox_options=options)
    return driver


def get_links(soup):
    """
    returns a set of all the property links from a magic_bricks webpage soup
    """
    all_links = []
    for a_element in soup.find_all('a', {'class': 'm-srp-card__title'}):
        all_links.append(a_element['href'])
    return set(all_links)


def get_homepage(driver, headless=True):
    """
    returns firefox webdriver with home page of magic bricks
    """
    try:
        driver.get('https://www.magicbricks.com')

    except seleniumExceptions.SessionNotCreatedException:
        logger_exc.error(
            'something is wrong with webdriver. Therefore relaunched webdriver.')
        driver = get_driver(headless=headless)
        driver.get('https://www.magicbricks.com')
    return driver


def select_prop_type(homepage_driver):
    prop_type = homepage_driver.find_element_by_id("buy_proertyTypeDefault")
    prop_type.click()
    pan = homepage_driver.find_element_by_id("propType_buy")
    check_boxes = pan.find_elements_by_class_name("checkBox")
    for check_box in check_boxes:
        check_box.click()
    prop_type.click()
    return homepage_driver

def get_searchbox_and_button(driver):
    """
    returns search box and search button element (from magic_bricks home page)
    """
    search_box = driver.find_element(by='id', value='keyword')
    button = driver.find_element_by_id('btnPropertySearch')
    return search_box, button


def click_button(button):
    """
    clicks the search button of magic bricks homepage
    (sometimes it takes 2 clicks after entering something in search box
    to trigerthe search)
    """
    try:
        button.click()
        button.click()

    except seleniumExceptions.StaleElementReferenceException:
        pass


def get_magiclinks(regions, file_path, headless=True, threshold=None):
    """
    takes a sequence of suggested regions by magic bricks search engine and file path of the output file to which the magic property links will be 
    written(append mode)
    """

    if threshold is None:
        threshold = 3000

    temp_thresh = threshold
    driver = get_driver(headless=headless)
    regions_done = 0
    magic_links = set()
    start_time = time.time()
    old_links = set()
    for region in regions:
        try:
            driver = get_homepage(driver, headless=headless)
            driver = select_prop_type(driver)
            search_box, button = get_searchbox_and_button(driver)

            region = region.replace(',', '')
            search_box.clear()
            search_box.send_keys(region)

            click_button(button)
            time.sleep(1.5)

            if driver.current_url == 'https://www.magicbricks.com':
                logger_exc.error(
                    'webpage did not change on search button click for region - {}. Thus skipped this region'.format(region))
                continue

            region_hit_len = 0
            page_equate = []
            page_count = 0
            while True:

                soup = BeautifulSoup(driver.page_source, 'lxml')
                if soup:
                    add_links = get_links(soup)
                    magic_links.update(add_links)
                    region_hit_len += len(add_links)
                else:
                    logger_exc.error(
                        'didnt get soup for the url - {}'.format(driver.current_url()))
                    pass  # not break as if say due to some reasons if soup is None yet the webpage has next_button. Thus break should encounter when webpage doen't have any next_button
                try:
                    next_button = driver.find_element_by_link_text('Next Page')
                except seleniumExceptions.NoSuchElementException:
                    break
                else:
                    page_count += 1
                    page_equate.append(add_links)
                    next_button.click()
                    time.sleep(1.5)
                    # If three consecutive pages are same then leave the current region
                    if len(page_equate) == 3:
                        if (page_equate[0] == page_equate[1]) & (page_equate[1] == page_equate[2]): #
                            logger_info.info("Bresking out due to repeated pages for {} at ending page # {}".format(region, page_count))
                            break
                        else:
                            page_equate.pop(0)
                

            file_regions_hit = open('regions_hit_magic_links.txt', 'a')
            file_regions_hit.write('{}---{}'.format(region, region_hit_len))
            file_regions_hit.write('\n')
            file_regions_hit.close()

            regions_done += 1

            if len(magic_links) >= temp_thresh:
                new_links = magic_links - old_links
                old_links = magic_links.copy()
                file_connection = open(file_path, 'a')
                file_connection.write('\n'.join(new_links))
                file_connection.write('\n')
                file_connection.close()

                file_regions_hit = open('regions_hit_magic_links.txt', 'a')
                file_regions_hit.write("-----------ALL THE ABOVE REGIONS HAVE BEEN UPDATED---------")
                file_regions_hit.write('\n')
                file_regions_hit.close()

                end_time = time.time()
                time_taken = (end_time - start_time) / 60
                start_time = end_time
                logger_info.info('got additional {} links in {} min and total links are {} out of {} regions and total regions are {}'
                                 .format(len(new_links),time_taken, len(magic_links), regions_done, len(regions)))
                temp_thresh = len(magic_links) + threshold

            driver.delete_all_cookies()

        except seleniumExceptions.WebDriverException as e:
            logger_exc.error('got error with {}---{}'.format(region, e))
            print(e, '\n', region, '\n\n')

        except Exception as e:
            logger_exc.error('got error with {}---{}'.format(region, e))
            print(e, '\n', region, '\n\n')

    new_links = magic_links - old_links
    file_connection = open(file_path, 'a')
    file_connection.write('\n'.join(new_links))
    file_connection.close()
    
    file_regions_hit = open('regions_hit_magic_links.txt', 'a')
    file_regions_hit.write("-----------ALL THE ABOVE REGIONS HAVE BEEN UPDATED---------")
    file_regions_hit.write('\n')
    file_regions_hit.close()

    driver.close()


regions_file = open(sys.argv[1], 'r')  # sys.argv[1] is regions file path
regions = regions_file.read().split('\n')
regions_file.close()

file_path = sys.argv[3]  # sys.argv[3] is output file path
get_magiclinks(regions, file_path, headless=True, threshold=int(sys.argv[2]))
