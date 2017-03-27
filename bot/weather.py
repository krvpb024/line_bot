from linebot.models import *

from .utils import get_gz_api_data, get_api_data
import datetime, os, pprint

def get_weather(event, user, keyword):
    print('取得api')
    if isinstance(event.message, LocationMessage):
        data = get_api_data("https://api.darksky.net/forecast/{}/{},{}?lang=zh-tw&exclude=hourly&units=auto".format(os.environ["DARK_SKY_KEY"], str(event.message.latitude), str(event.message.longitude)))
    elif isinstance(event.message, TextMessage):
        data = get_api_data("https://api.darksky.net/forecast/{}/{},{}?lang=zh-tw&exclude=hourly&units=auto".format(os.environ["DARK_SKY_KEY"], str(user.latitude), str(user.longitude)))


    weekday_dict = {'0':'周日', '1':'周一', '2':'周二', '3':'周三', '4':'周四', '5':'周五', '6':'周六'}


    # ['3', '4', '5', '6', '0', '1', '2', '3']
    weekday_list = [str(datetime.datetime.fromtimestamp(int(x['time'])).strftime('%w')) for x in data['daily']['data']]
    print(weekday_list)



    converted_weekday_dict = {weekday_dict[item]:index for index, item in enumerate(weekday_list)}
    converted_weekday_dict.update({'現在':0})
    converted_weekday_dict.update({'今天':0})
    converted_weekday_dict.update({'明天':1})
    converted_weekday_dict.update({'後天':2})
    converted_weekday_dict.update({'大後天':3})
    converted_weekday_dict.update({'下周':7})
    print(converted_weekday_dict)

    # {'周三': '3', '周四': '4', '周五': '5', '周六': '6', '周日': '0', '周一': '1', '周二': '2', '今天': '3', '明天': '4', '後天': '5'}
    weekday = weekday_dict[str(datetime.datetime.fromtimestamp(int(data['daily']['data'][int(converted_weekday_dict[keyword])]['time'])).strftime('%w'))]
    # text 要用的
    date = datetime.datetime.fromtimestamp(int(data['daily']['data'][int(converted_weekday_dict[keyword])]['time'])).strftime('%Y/%m/%d')


    print('取得資料')

    if converted_weekday_dict[keyword] == 0:
        temperature = round(data['currently']['temperature'])
        precipprobability = round(data['currently']['precipProbability'] *100)
    else:
        precipprobability = round(data['daily']['data'][int(converted_weekday_dict[keyword])]['precipProbability'] *100)
    weather = data['daily']['data'][int(converted_weekday_dict[keyword])]['summary']
    summary = data['daily']['summary']
    temperaturemax = round(data['daily']['data'][int(converted_weekday_dict[keyword])]['temperatureMax'])
    temperaturemin = round(data['daily']['data'][int(converted_weekday_dict[keyword])]['temperatureMin'])
    print('回傳')



    user.status = ""
    user.save()
    if converted_weekday_dict[keyword] == 0:
        text = str(date + " " + weekday + "\n"
        "天氣概況：\n" + weather + "\n" +
        "現在氣溫：" + str(temperature) + "°C\n\n" +
        "今天最高溫為：" + str(temperaturemax) + "°C\n" +
        "今天最低溫為：" + str(temperaturemin) + "°C\n" +
        "降雨機率為：" + str(precipprobability) + "%\n\n" +
        summary
        )
    else:
        text = str(date + " " + weekday + "\n"
        "天氣概況：\n" + weather + "\n" +
        "最高溫為：" + str(temperaturemax) + "°C\n" +
        "最低溫為：" + str(temperaturemin) + "°C\n" +
        "降雨機率為：" + str(precipprobability) + "%"
        )

    return text
