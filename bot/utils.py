from oauth2client.service_account import ServiceAccountCredentials

from urllib.request import urlopen
import urllib, json, pprint, re, time, gzip, datetime

def get_gz_api_data(api):
    response = urlopen(api)
    with gzip.open(response, 'r') as taipei_bus:
        json_bytes = taipei_bus.read()
        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)

        return data

def get_api_data(api):
    api = api
    result = urlopen(api).read()
    data = json.loads(result)

    return data

def get_file_data(file):
    with open (file) as f:
        result = json.load(f)
    return result

def get_current_time(format):
    current_time = datetime.datetime.now().strftime(format)
    return current_time

def replace_word(message, type):
    replace_message = message
    if type == "address":
        replace_dict = {'臺':'台', '區':'', '鄉':'', '鎮':'', '市':'', '縣':''}
    elif type == "day":
        replace_dict = {'星期':'周', '禮拜':'周', '週':'周', '星期天':'周日','禮拜天':'周日',}


    for keyword in replace_dict.keys():
        if keyword in replace_message:
            replace_message = replace_message.replace(keyword, replace_dict[keyword])

    return replace_message

def get_taiwan_city():
    with open ('json/taiwan_city.json') as f:
        taiwan_city_dict = json.load(f)
    city_list = [x for x in taiwan_city_dict.keys()]
    return city_list

def get_taiwan_city_name():
    city_list = get_taiwan_city()
    city_name_list = [replace_word(x, "address") for x in city_list]

    return city_name_list


def get_taiwan_dist():
    with open ('json/taiwan_city.json') as f:
        taiwan_city_dict = json.load(f)
    dist_list = [y for x in taiwan_city_dict.values() for y in x]
    return dist_list

def get_taiwan_dist_name():
    dist_name = get_taiwan_dist()
    dist_name_list = [replace_word(x, "address") for x in dist_name]

    return dist_name_list
