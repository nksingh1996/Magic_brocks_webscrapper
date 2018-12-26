import sys
from bs4 import BeautifulSoup
import requests
import json
import re
import logging

filehandler_except = logging.FileHandler('exceptions.log')
filehandler_info = logging.FileHandler('info.log')

logging.basicConfig(filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

logger_exc = logging.getLogger('exceptions')
logger_exc.addHandler(filehandler_except)

logger_info = logging.getLogger('info')
logger_info.addHandler(filehandler_info)


def get_string(tag):
    string = tag.string if tag else None
    if string:
        string = re.sub(r'[\n]+|[\xa0]+', '', string).strip()

    return string


def get_pinfo(soup):

    prop_info_col = soup.find('div', {'class': 'propInfoBlockInn'})
    p_infoColumn_list = prop_info_col.find_all(
        'div', {'class': 'p_infoColumn'})

    prop_info_row = soup.find('div', {'class': 'descriptionCont'})
    p_infoRow_list = prop_info_row.find_all('div', {'class': 'p_infoRow'})[1:]

    return p_infoColumn_list, p_infoRow_list


def get_location(soup):
    latitude = soup.find('meta', {'itemprop': 'latitude'}).get('content', None)
    longitude = soup.find(
        'meta', {'itemprop': 'longitude'}).get('content', None)
    return {'location': {'latitude': longitude, 'longitude': latitude}}


def get_columns(p_infoColumn_list):
    prop_col = {}

    for col in p_infoColumn_list:

        col_title = get_string(col.find('div', {'class': 'p_title'}))
        col_value = get_string(col.find('div', {'class': 'p_value'}))

        if col_title == 'Super area':
            area = get_string(col.find('span', {'id': 'coveredAreaDisplay'}))
            unit = get_string(col.find('span', {'class': 'areaInputType'}))

            if all([area, unit]):
                area = area + ' ' + unit
            else:
                None

            rate = get_string(
                col.find('div', {'class': 'fo_11px c_dark_gray'}))
            col_value = {'area': area, 'rate': rate}

        if col_title == 'Carpet area':
            area = get_string(col.find('span', {'id': 'carpetAreaDisplay'}))
            unit = get_string(col.find('span', {'class': 'areaInputType'}))

            if all([area, unit]):
                area = area + ' ' + unit
            else:
                None

            rate = get_string(
                col.find('div', {'class': 'fo_11px c_dark_gray'}))
            col_value = {'area': area, 'rate': rate}

        if col_title == 'Bedrooms':
            bedrooms = col.find('div', {'class': 'p_value'}).find_all(
                'span', {'class': 'bedroomVal'})
            col_value = tuple(map(lambda x: get_string(x), bedrooms))

        prop_col[col_title] = col_value

    return prop_col


def get_rows(p_infoRow_list):
    prop_row = {}

    for row in p_infoRow_list:

        row_title = get_string(row.find('div', {'class': 'p_title'}))
        row_value = get_string(row.find('div', {'class': 'p_value'}))

        if row_title == 'Address':
            row_value = row.find('div', {'class': 'p_value'})
            row_value = row_value.contents[0]

        if row_title == 'Price Breakup':
            prices = row.find_all('span', {'class': 'breakupdivider'})
            price_break = tuple(map(lambda p: get_string(
                p.find('span', 'semiBold')) + p.contents[-1], prices))
            row_value = price_break

        if row_title:
            row_title = re.sub(r'\n|\xa0', '', row_title.strip())

        if isinstance(row_value, str):
            row_value = re.sub(r'\n|\xa0', '', row_value.strip())

        elif isinstance(row_value, tuple):
            row_value = tuple(map(lambda x: re.sub(
                r'\n|\xa0', '', x.strip()), row_value))

        prop_row[row_title] = row_value

    return prop_row


def get_quick_facts(soup):
    quick_facts = soup.find(
        'div', {'id': 'quickFactsOnProperty', 'class': 'quickFacts'})
    columns = quick_facts.find_all('div', {'class': 'column'})
    data = {}

    for col in columns:
        label = re.sub(r'[\n]+|[\xa0]+', ' ',
                       col.find('div', 'pc_label').text).strip()
        value = re.sub(r'[\n]+|[\xa0]+', ' ',
                       col.find('div', 'pc_value').text).strip()
        data[label] = value
    return data


def get_links(links_file_path):
    file = open(links_file_path, 'r')
    links = file.read().split('\n')
    file.close()
    return links


links_file_path = sys.argv[1]
all_links = get_links(links_file_path)

error_file_path = sys.argv[3]
output_file_path = sys.argv[2]

for link in all_links:

    text = requests.get(link).text
    soup = BeautifulSoup(text, 'lxml')

    if soup is None:
        continue

    try:
        p_infoColumn_list, p_infoRow_list = get_pinfo(soup)

        prop_info_col = get_columns(p_infoColumn_list)
        prop_info_row = get_rows(p_infoRow_list)
        location = get_location(soup)
        quick_facts = get_quick_facts(soup)

    except AttributeError as e:
        error = open(error_file_path, "w")
        error.write(link + '\n')
        error.close()
        print(e, link, '\n')

    else:

        prop_info_col.update(prop_info_row)
        prop_info_col.update(location)
        prop_info_col.update(quick_facts)

        if 'Loan Offered by' in prop_info_col:
            del prop_info_col['Loan Offered by']

        if 'None' in prop_info_col:
            del prop_info_col['None']

        output_file = open(output_file_path, "w")
        json.dump(prop_info_col, output_file)
        output_file.close()
