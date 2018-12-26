from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import logging
import time
import file_generator
import sys
import itertools
"""
using sys takes inputs from command line and coomands template -
python3 filename.py regions/districts regions_input_path_file threshold(no. of regions search
 after which data will be wriiten in files) output_path_file_for_suggestions
                            OR
python3 filename.py permutations int_value_for_number_of_char_in_permutation(preferably = 3)  threshold output_file_path
"""
logging.basicConfig(filename='extracting_regions.log',
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def get_webdriver(url=None, headless=True):
    """
    takes a url and headless option and launches firefox(gecko driver)
    webdriver with the given url(default url = 'https://www.magicbricks.com/'
    and headless = False)
    """

    if not url:
        url = 'https://www.magicbricks.com/'

    # setting firefox webdriver options
    options = Options()
    options.set_headless(headless=headless)

    # launching firefox and get url
    driver = webdriver.Firefox(firefox_options=options)
    driver.get(url)
    driver.delete_all_cookies()
    logging.info('driver launched')

    return driver


def search_regions(regions, file_path, headless=True, threshold=None):
    """
    takes a sequence of regions and returns a dictionary(regions as key)
    of number of suggestions from magic bricks search engine against each
    region name and also a set of all suggestions
    """

    if threshold is None:
        threshold = 2000
    driver = get_webdriver(headless=headless)
    search = driver.find_element_by_id('keyword')  # search box element
    suggestion_box = driver.find_element_by_id(
        'keyword_suggest')  # suggestion box element
    logging.info('search and suggestion objects created')

    # data will contain all suggestions
    data = set()
    regions_hit = dict()
    start_time = time.time()
    i = 0
    old_data = set()

    for region in regions:
                # what if passed an iterator
                # needs to discuss pause time
        i += 1

        search.clear()
        search.send_keys(region)
        time.sleep(0.4)
        # getting suggestion(note: element at 0 index is either blank or
        # 'LOCATION' thus leaving it)
        suggest_data = suggestion_box.text.split('\n')[1:]
        file_regions_hit = open('regions_hit.txt', 'a')
        file_regions_hit.write('{}---{}'.format(region, len(suggest_data)))
        file_regions_hit.write('\n')
        file_regions_hit.close()

        regions_hit[region] = len(suggest_data)

        data.update(suggest_data)

        if i % threshold == 0:
            new_data = data - old_data
            old_data = data.copy()
            file_connection = open(file_path, 'a')
            file_connection.write('\n'.join(new_data))
            file_connection.write('\n')
            file_connection.close()

            file_regions_hit = open('regions_hit.txt', 'a')
            file_regions_hit.write("-----------ALL THE ABOVE REGIONS HAVE BEEN UPDATED---------")
            file_regions_hit.write('\n')
            file_regions_hit.close()

            end_time = time.time()
            logging.info('{} regions done out of {} regions in additional {}\
                min and total unique suggestions are {}'
                         .format(i, len(regions), (end_time - start_time) / 60,
                                 len(data)))
            start_time = end_time

    driver.close()
    logging.info('all regions searched and {} regions have zero suggestions and\
        total unique areas suggested are {}'
                 .format(list(regions_hit.values()).count(0), len(data)))
    new_data = data - old_data
    file_connection = open(file_path, 'a')
    file_connection.write('\n'.join(new_data))
    file_connection.close()


if sys.argv[1] == 'permutations':
    logging.info("regions_extraction from magic bricks search engine has\
        started with permutation")
    alphabets = [chr(x) for x in range(ord('a'), ord('z') + 1)]
    permutations = set(itertools.permutations(alphabets * 2, int(sys.argv[2])))
    file_path = sys.argv[4]
    # sys_argv[4] is file path to which output is saved
    search_regions(permutations, file_path, threshold = int(sys.argv[3]), headless = True)


else:
    logging.info("regions_extraction from magic bricks search engine has\
        started with {}".format(sys.argv[1]))
    if sys.argv[1] == 'districts':
        regions = file_generator.get_regions('districts', sys.argv[2])
        # sys.argv[2] is file path of regions json file
    elif sys.argv[1] == 'regions':
        regions = (file_generator.get_regions('regions', sys.argv[2]))

    file_path = sys.argv[4]
    file_regions_hit = open('regions_hit.txt', 'a')
    # sys_argv[4] is file path to which output is saved
    search_regions(regions, file_path, threshold = int(sys.argv[3]), headless = True)
