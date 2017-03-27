from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

from .models import UserProfile, DayKeyWord

from urllib.request import urlopen
import urllib, json, pprint, re, time, gzip, datetime

from .utils import get_gz_api_data, get_api_data, get_current_time, get_taiwan_city, get_taiwan_city_name, replace_word, get_file_data, get_taiwan_dist_name
from .weather import get_weather


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    print('確認method')
    if request.method == 'POST':
        #request.META 記錄了本次HTTP request 的 Header 訊息 例如：IP
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        # Handler when receiver Line Message
        print('確認signature')
        try:
            events = parser.parse(body, signature)

        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()



        for event in events:
            print("這是event {}".format(event))
            print('獲得個人資料')
            profile = line_bot_api.get_profile(event.source.user_id)



            if isinstance(event, FollowEvent):
                user, created = UserProfile.objects.get_or_create(user_id=profile.user_id, user_name=profile.display_name)
                print(user.user_id)
                print(user.user_name)
                print(created)
                if created == True:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=
                        "哈囉！{}\n很高興認識你，請告訴我你需要什麼協助".format(user.user_name)
                        )
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=
                        "哈囉！{}\n好久不見，歡迎回來".format(user.user_name)
                        )
                    )

            print('如果是訊息')
            if isinstance(event, MessageEvent):
                user, created = UserProfile.objects.get_or_create(user_id=profile.user_id, user_name=profile.display_name)

                if isinstance(event.message, TextMessage):

                    if event.message.text == "hi":
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=
                            "你需要什麼幫助呢？\n" +
                            "我可以幫你查詢：\n\n" +
                            "天氣\n" +
                            "空氣品質\n" +
                            "公車到站時間"
                            )
                        )

                    elif "位置" in event.message.text or "地區" in event.message.text or "地點" in event.message.text or "位子" in event.message.text:

                        if "設定" in event.message.text:
                            if '取消' in event.message.text or '刪除' in event.message.text or '移除' in event.message.text:
                                if user.latitude and user.longitude:
                                    user.latitude = ''
                                    user.longitude = ''
                                    user.status = ''
                                    user.save()
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(text='位置設定已取消')
                                    )
                                elif user.latitude == '' and user.longitude == '':
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(text='你還沒有設定你的位置，我沒有東西可以取消')
                                    )
                            if user.latitude and user.longitude:
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TemplateSendMessage(
                                    alt_text='Confirm template',
                                    template=ConfirmTemplate(
                                        text='你已經設定過你的位置了\n請問需要重新設定嗎？',
                                        actions=[
                                            PostbackTemplateAction(
                                                label='確定',
                                                text='是的，我要重新設定',
                                                data='重新設定位置'
                                            ),
                                            MessageTemplateAction(
                                                label='取消',
                                                text='不用，謝謝'
                                            )
                                        ]
                                    )
                                )
                                )

                            else:
                                user.status = "設定位置"
                                user.save()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text="傳送位置訊息給我，我會記錄你的位置。以後我就可以根據你設定的位置提供你所需要的服務")
                                )


                        if '取消' in event.message.text or '刪除' in event.message.text or '移除' in event.message.text:
                            if user.latitude and user.longitude:
                                user.latitude = ''
                                user.longitude = ''
                                user.status = ''
                                user.save()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text='位置設定已取消')
                                )
                            elif user.latitude == '' and user.longitude == '':
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text='你還沒有設定你的位置，我沒有東西可以取消')
                                )

                    elif "天氣" in event.message.text or "氣溫" in event.message.text or "溫度" in event.message.text:
                        day_key_word = [word.keyword for word in DayKeyWord.objects.all()]
                        message = replace_word(event.message.text, "day")
                        message = replace_word(message, "address")
                        city_name = get_taiwan_city_name()
                        dist_name = get_taiwan_dist_name()
                        print(message)
                        user.status = "天氣"
                        user.save()

                        print(message)
                        matches = [x for x in day_key_word if x in message]
                        print(matches)


                        if any(x in message for x in city_name) or any(x in message for x in dist_name):

                            user.status = "天氣 地區查詢"
                            user.save()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=
                                "我還沒有辦法直接查詢地區的天氣，請直接傳送位置訊息給我，我就可以幫你查詢"
                                )
                            )


                        if matches:
                            for keyword in matches:
                                user.status += " " + keyword
                                user.save()


                            if user.latitude == '' and user.longitude == '' and not user.status.startswith("天氣 地區查詢"):
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text=
                                    "請直接傳送位置訊息，我就可以幫你查詢該地天氣\n\n或是設定你的查詢位置，以後只要問我天氣，我就會依照你設定的位置幫你查詢"
                                    )
                                )
                            else:
                                if not user.status.startswith("天氣 地區查詢"):
                                    for keyword in day_key_word:
                                        if keyword in message:
                                            text = get_weather(event, user, keyword)
                                            line_bot_api.reply_message(
                                                event.reply_token,
                                                TextSendMessage(text=text)
                                            )

                        else:
                            if not user.status.startswith("天氣 地區查詢"):
                                if user.latitude == '' and user.longitude == '':
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(text=
                                        "請直接傳送位置訊息，我就可以幫你查詢該地天氣\n\n或是設定你的查詢位置，以後只要問我天氣，我就會依照你設定的位置幫你查詢"
                                        )
                                    )
                                else:
                                    text = get_weather(event, user, '今天')
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(text=text)
                                    )





                    elif event.message.text.startswith("公車"):
                        try:
                            bus = event.message.text.split()[1]
                            stop = event.message.text.split()[2]
                            data = get_gz_api_data('http://data.taipei/bus/ROUTE')

                            found = [dict([("id", d["Id"]), ("departure", d["departureZh"]), ("destination", d["destinationZh"]), ("provider", d["providerName"])]) for d in data["BusInfo"] if d["nameZh"] == bus][0]
                            # pprint.pprint(found)

                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                alt_text='Confirm template',
                                template=ConfirmTemplate(
                                    text='要往哪個方向？',
                                    actions=[
                                        PostbackTemplateAction(
                                            label=found["departure"],
                                            text=found["departure"],
                                            data="bus " + str(found["id"]) + " 1 " + stop
                                        ),
                                        PostbackTemplateAction(
                                            label=found["destination"],
                                            text=found["destination"],
                                            data="bus " + str(found["id"]) + " 0 " + stop
                                        )
                                        ]
                                    )
                                )
                            )
                        except IndexError:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="請輸入正確格式")
                            )



                    elif "空氣品質" in event.message.text or "pm2.5" in event.message.text:
                        user.status = "空氣品質"
                        user.save()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TemplateSendMessage(
                                    alt_text='Carousel template',
                                    template=CarouselTemplate(
                                        columns=[
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/3/3b/Smog_in_Beijing_CBD.JPG',
                                                title='pm2.5',
                                                text='請選擇地區',
                                                actions=[
                                                    MessageTemplateAction(
                                                        label='北',
                                                        text='北'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='中',
                                                        text='中'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='南',
                                                        text='南'
                                                    )
                                                ]
                                            ),
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/3/3b/Smog_in_Beijing_CBD.JPG',
                                                title='pm2.5',
                                                text='請選擇地區',
                                                actions=[
                                                        MessageTemplateAction(
                                                            label='東',
                                                            text='東'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='離島',
                                                            text='離島'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='——',
                                                            text=' '
                                                                        )
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    )
                                                )


                    if user.status.startswith('空氣品質'):

                        if event.message.text == "北":
                            print('如果是北')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                    alt_text='Carousel template',
                                    template=CarouselTemplate(
                                        columns=[
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Northern_Taiwan_official_determined.svg/220px-Northern_Taiwan_official_determined.svg.png',
                                                title='北台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                    MessageTemplateAction(
                                                        label='臺北市',
                                                        text='臺北市'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='新北市',
                                                        text='新北市'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='基隆市',
                                                        text='基隆'
                                                    )
                                                ]
                                            ),
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Northern_Taiwan_official_determined.svg/220px-Northern_Taiwan_official_determined.svg.png',
                                                title='北台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                        MessageTemplateAction(
                                                            label='桃園市',
                                                            text='桃園市'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='新竹縣',
                                                            text='新竹縣'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='新竹市',
                                                            text='新竹市'
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    )
                                )


                        elif event.message.text == "中":
                            print('如果是中')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                    alt_text='Carousel template',
                                    template=CarouselTemplate(
                                        columns=[
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Central_Taiwan_official_determined.svg/250px-Central_Taiwan_official_determined.svg.png',
                                                title='中台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                    MessageTemplateAction(
                                                        label='苗栗縣',
                                                        text='苗栗縣'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='臺中市',
                                                        text='臺中市'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='彰化縣',
                                                        text='彰化縣'
                                                    )
                                                ]
                                            ),
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Central_Taiwan_official_determined.svg/250px-Central_Taiwan_official_determined.svg.png',
                                                title='中台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                        MessageTemplateAction(
                                                            label='南投縣',
                                                            text='南投縣'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='雲林縣',
                                                            text='雲林縣'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='——',
                                                            text=' '
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    )
                                )


                        elif event.message.text == "南":
                            print('如果是南')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                    alt_text='Carousel template',
                                    template=CarouselTemplate(
                                        columns=[
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Southern_Taiwan_official_determined.svg/220px-Southern_Taiwan_official_determined.svg.png',
                                                title='南台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                    MessageTemplateAction(
                                                        label='嘉義縣',
                                                        text='嘉義縣'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='嘉義市',
                                                        text='嘉義市'
                                                    ),
                                                    MessageTemplateAction(
                                                        label='臺南市',
                                                        text='臺南市'
                                                    )
                                                ]
                                            ),
                                            CarouselColumn(
                                                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Southern_Taiwan_official_determined.svg/220px-Southern_Taiwan_official_determined.svg.png',
                                                title='南台灣',
                                                text='請選擇縣市',
                                                actions=[
                                                        MessageTemplateAction(
                                                            label='高雄市',
                                                            text='高雄市'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='屏東縣',
                                                            text='屏東縣'
                                                        ),
                                                        MessageTemplateAction(
                                                            label='——',
                                                            text=' '
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    )
                                )


                        elif event.message.text == "東":
                            print('如果是東')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                    alt_text='Buttons template',
                                    template=ButtonsTemplate(
                                        thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Eastern_Taiwan_official_determined.svg/220px-Eastern_Taiwan_official_determined.svg.png',
                                        title='東台灣',
                                        text='請選擇縣市',
                                        actions=[
                                            MessageTemplateAction(
                                                label='花蓮縣',
                                                text='花蓮'
                                            ),
                                            MessageTemplateAction(
                                                label='臺東縣',
                                                text='臺東'
                                            )
                                        ]
                                    )
                                )
                            )

                        elif event.message.text == "離島":
                            print('如果是離島')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TemplateSendMessage(
                                    alt_text='Buttons template',
                                    template=ButtonsTemplate(
                                        thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Penghu_201506.jpg/800px-Penghu_201506.jpg',
                                        title='離島',
                                        text='請選擇縣市',
                                        actions=[
                                            MessageTemplateAction(
                                                label='金門縣',
                                                text='金門'
                                            ),
                                            MessageTemplateAction(
                                                label='連江縣',
                                                text='馬祖'
                                            ),
                                            MessageTemplateAction(
                                                label='澎湖縣',
                                                text='馬公'
                                            )
                                        ]
                                    )
                                )
                            )

                        county_site = get_file_data('json/pm.json')


                        print('要查哪些城市')
                        if event.message.text in list(item for item in county_site.keys()):
                            user.status += " " + event.message.text
                            user.save()
                            print('要查城市有哪些地區')
                            site_list = county_site[event.message.text]
                            text = "請告訴我哪個監測站離你最近\n\n"
                            for site in site_list:
                                text += site + "\n"
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=text)
                            )

                        if re.match(r"空氣品質\s\w+", user.status) and event.message.text in county_site[user.status.split()[1]]:
                            print('取得pm data')
                            data = get_api_data("http://opendata.epa.gov.tw/ws/Data/REWXQA/?$orderby=SiteName&$skip=0&$top=1000&format=json")
                            print('拿到pm data')
                            pm = next((item for item in data if item["SiteName"] == event.message.text))
                            print(pm)
                            user.status = ""
                            user.save()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=
                                event.message.text + "\n"
                                "目前PM2.5濃度為：" + pm["PM2.5"] + "\n" +
                                "狀態為：" + pm["Status"]
                                )
                            )



                elif isinstance(event.message, LocationMessage):
                    if user.status.startswith('天氣'):
                        if len(user.status.split()) >= 2:
                            if "地區查詢" not in user.status:
                                keyword = user.status.split()[1]
                                text = get_weather(event, user, keyword)
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text=text)
                                )
                            elif "地區查詢" in user.status and len(user.status.split()) >= 3:
                                keyword = user.status.split()[2]
                                text = get_weather(event, user, keyword)
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text=text)
                                )
                            elif user.status.startswith('天氣 地區查詢'):
                                text = get_weather(event, user, '今天')
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text=text)
                                )
                        elif user.status == '天氣':
                            text = get_weather(event, user, '今天')
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=text)
                            )

                    elif user.status.startswith('設定位置'):
                        user.latitude = event.message.latitude
                        user.longitude = event.message.longitude
                        user.status = ''
                        user.save()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='位置設定完成，現在我會根據你設定的位置查詢天氣')
                        )




            elif isinstance(event, PostbackEvent):
                user, created = UserProfile.objects.get_or_create(user_id=profile.user_id, user_name=profile.display_name)
                if event.postback.data.startswith("bus"):
                    post_data = event.postback.data.split() # ['bus', '11411', '1', '中華路口'] bus routeId GoBack 0為去程(要去目的地) 1為返程(要去出發點)

                    print(post_data)
                    data = get_gz_api_data('http://data.taipei/bus/Stop')
                    found = [d["Id"] for d in data["BusInfo"] if d["routeId"] == int(post_data[1]) and d["nameZh"] == post_data[3] and d["goBack"] == post_data[2]][0]

                    print(found)

                    time_data = get_gz_api_data('http://data.taipei/bus/EstimateTime')


                    time_found = [d["EstimateTime"] for d in time_data["BusInfo"] if d["StopID"] == int(found)][0]
                    waiting_time = time.strftime('%-M', time.gmtime(int(time_found)))

                    if waiting_time == "0":
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=
                            "即將到站"
                            )
                        )
                    else:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=
                            "目前還需等候：\n{}分鐘".format(waiting_time)
                            )
                        )
                if event.postback.data == '重新設定位置':
                    user.status = "設定位置"
                    user.save()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='傳送位置訊息給我，我會記錄你的位置。以後我就可以根據你設定的位置提供你所需要的服務')
                    )


        return HttpResponse()
    else:
        return HttpResponseBadRequest()
