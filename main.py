import telebot
import config
import yandex_weather_api
import requests as req
import sqlite3
import schedule
import time
from telebot import types


bot = telebot.TeleBot(config.BOT_TOKEN)
status_search = 0
city_now = ''
city = ''
user = ''
us_id = 0
eng_dir = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'c']
rus_dir = ['северо-западный', 'северный', 'северо-восточный', 'восточный', 'юго-восточный', 'южный', 'юго-западный',
           'западный', 'штиль']
prec = ['без осадков', 'дождь', 'дождь со снегом', 'снег', 'град']


def insert_into_db(info):
    try:
        print(info)
        sqlite_connection = sqlite3.connect('user_times.db')
        cursor = sqlite_connection.cursor()
        sqlite_insert_query = """INSERT INTO times
                                         (id, name, address, send_time)
                                         VALUES (?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_query, info)
        sqlite_connection.commit()
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def delete_from_db(info):
    try:
        sqlite_connection = sqlite3.connect('user_times.db')
        cursor = sqlite_connection.cursor()
        print("Подключен к SQLite")

        sql_update_query = """DELETE from times where id = ?"""
        cursor.execute(sql_update_query, (info, ))
        sqlite_connection.commit()
        print("Запись успешно удалена")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def update_db(info):
    ch_address, ch_time, ch_id = info
    try:
        sqlite_connection = sqlite3.connect('user_times.db')
        cursor = sqlite_connection.cursor()

        sql_update_query = """Update times set address = ? where id = ?"""
        data = (ch_address, ch_id)
        cursor.execute(sql_update_query, data)

        sql_update_query = """Update times set send_time = ? where id = ?"""
        data = (ch_time, ch_id)
        cursor.execute(sql_update_query, data)

        sqlite_connection.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def is_valid_time(us_time):
    if ':' in us_time:
        a = us_time.split(':')
        if a[0].isdigit():
            if len(a[0]) == 2 and a[0][0] == '0':
                a[0] = a[0][1]
            if len(a[1]) == 2 and a[1][0] == '0':
                a[1] = a[1][1]
            if 0 <= int(a[0]) < 24 and 0 <= int(a[1]) < 60:
                return True
            else:
                return False
        else:
            return False
    else:
        return False


def address_to_position(toponim):  # отвечает за перевод адресса в географические координаты
    place = toponim
    b = req.get("https://geocode-maps.yandex.ru/1.x/?apikey=" + config.GEOCODE_TOKEN + "&geocode=" + place +
                "&format=json").json()
    x, y = b["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split()
    return [y, x]


def get_weather(cords, day):  # функция получения погоды по координатам места
    a = yandex_weather_api.get(req, config.WEATHER_TOKEN, rate='forecast', lat=cords[0], lon=cords[1])
    if day != -1:
        info = a["forecasts"][day]
        date = '.'.join(info["date"].split('-')[::-1])

        night_temp = info["parts"]["night"]["temp_avg"]
        night_windd = rus_dir[eng_dir.index(info["parts"]["night"]["wind_dir"])]
        night_winds = info["parts"]["night"]["wind_speed"]
        night_prec = prec[int(info["parts"]["night"]["prec_type"])]
        night = "🌙 Ночь:\nТемпература воздуха: " + str(int(round(night_temp, 0))) + ' ℃\nВетер: ' + night_windd + ' '\
                + str(
            night_winds) + ' м/с\nОсадки: ' + night_prec + '\n'

        morning_temp = info["parts"]["morning"]["temp_avg"]
        morning_windd = rus_dir[eng_dir.index(info["parts"]["morning"]["wind_dir"])]
        morning_winds = info["parts"]["morning"]["wind_speed"]
        morning_prec = prec[int(info["parts"]["morning"]["prec_type"])]
        morning = "🌅 Утро:\nТемпература воздуха: " + str(int(round(morning_temp, 0))) + ' ℃\nВетер: ' + morning_windd\
                  + ' ' + str(
            morning_winds) + ' м/с\nОсадки: ' + morning_prec + '\n'

        day_temp = info["parts"]["day"]["temp_avg"]
        day_windd = rus_dir[eng_dir.index(info["parts"]["day"]["wind_dir"])]
        day_winds = info["parts"]["day"]["wind_speed"]
        day_prec = prec[int(info["parts"]["day"]["prec_type"])]
        day = "☀ День:\nТемпература воздуха: " + str(int(round(day_temp, 0))) + ' ℃\nВетер: ' + day_windd + ' ' + str(
            day_winds) + ' м/с\nОсадки: ' + day_prec + '\n'

        evening_temp = info["parts"]["evening"]["temp_avg"]
        evening_windd = rus_dir[eng_dir.index(info["parts"]["evening"]["wind_dir"])]
        evening_winds = info["parts"]["evening"]["wind_speed"]
        evening_prec = prec[int(info["parts"]["evening"]["prec_type"])]
        evening = "🌇 Вечер:\nТемпература воздуха: " + str(int(round(evening_temp, 0))) + ' ℃\nВетер: ' + evening_windd\
                  + ' ' + str(
            evening_winds) + ' м/с\nОсадки: ' + evening_prec

        answer = "Погода на " + date + ":\n" + night + morning + day + evening
    else:
        info = a["fact"]
        real_temp = info["temp"]
        feel_temp = info["feels_like"]
        wind_speed = info["wind_speed"]
        wind_dir = rus_dir[eng_dir.index(info["wind_dir"])]
        humidity = info["humidity"]
        prec_type = prec[int(info["prec_type"])]
        answer = "Сейчас в " + city_now + ":\n🌡 Температура воздуха: " + str(int(round(real_temp, 0))) +\
                 ' ℃\n🌡 Ощущаемая температура: ' + str(int(round(feel_temp, 0))) + ' ℃\n💨 Ветер: ' + wind_dir + ' '\
                 + str(wind_speed) + ' м/с\n🌧 Осадки: ' + prec_type + '\n💦 Влажность воздуха: ' + str(humidity) + '%'
    return answer


def menu():  # возращает главную клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Узнать текущую погоду")
    button2 = types.KeyboardButton("Узнавать погоду ежеднeвно")
    button3 = types.KeyboardButton("Информация")

    markup.add(button1, button2, button3)
    return markup



@bot.message_handler(commands=['start'])
def welcome(message):  # приветственное сообщение
    welcome_stic = open('welcome.tgs', 'rb')
    bot.send_sticker(message.chat.id, welcome_stic)
    markup = menu()
    bot.send_message(message.chat.id, "Приветствую, <b>{0.first_name}</b>!\n<b>{1.first_name}</b> - это бот созданный"
                                      " для отслеживания погоды в разных уголках мира!".format(message.from_user,
                                                                                               bot.get_me()),
                     parse_mode='html', reply_markup=markup)

    curs = sqlite3.connect('user_times.db').cursor()
    if curs.execute('SELECT * FROM times WHERE id=?', (message.from_user.id, )).fetchone():
        try:
            sqlite_connection = sqlite3.connect('user_times.db')
            cursor = sqlite_connection.cursor()
            print("Подключен к SQLite")

            sql_select_query = """select * from times where id = ?"""
            cursor.execute(sql_select_query, (message.from_user.id,))
            data = cursor.fetchall()
            schedule.every().day.at(data[0][3]).do(bot.send_message(message.chat.id,
                                                                    get_weather(address_to_position(data[0][2]), 0)))
            cursor.close()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()
                print("Соединение с SQLite закрыто")



@bot.message_handler(content_types=['text'])
def messages(message):  # обработка сообщений
    global status_search, city_now, city, user, us_id
    curs = sqlite3.connect('user_times.db').cursor()
    if message.chat.type == 'private':
        us_id = message.from_user.id
        if message.text == 'Информация' and status_search == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Меню")
            markup.add(button1)
            bot.send_message(message.chat.id, "Данный бот создан в рамках хакатона <b>Geek Battle</b> от школы"
                                              " программирования <b>AllStack</b>.\nПроект разработал"
                                              " <a href=\"https://vk.com/iluchacha\">Щербаков Илья</a>(@iluchacha).",
                             parse_mode='html', reply_markup=markup)

        elif message.text == 'Узнать текущую погоду' and status_search == 0:
            bot.send_message(message.chat.id, 'Напишите ниже местоположение, где вы хотите узнать погоду:')
            status_search = 1  # Статус, отвечающий за поиск координат написанной пользователем локации

        elif message.text == 'Изменить данные' and status_search == 0:
            bot.send_message(message.chat.id, 'Напишите ниже местоположение, где вы хотите узнать погоду:')
            status_search = 5

        elif message.text == 'Отписаться от рассылки' and status_search == 0:
            delete_from_db(us_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Меню")
            markup.add(button1)
            bot.send_message(message.chat.id, 'Вы успешно отписались от рассылки!', reply_markup=markup)


        elif message.text == 'Узнавать погоду ежеднeвно' and status_search == 0 and not curs.execute('SELECT * FROM '
                                                                                                     'times WHERE id=?',
                                                                                                     (us_id, ))\
                .fetchone():
            bot.send_message(message.chat.id, 'Напишите ниже местоположение, где вы хотите узнать погоду:')
            status_search = 2

        elif message.text == 'Узнавать погоду ежеднeвно' and status_search == 0 and curs.execute('SELECT * FROM times '
                                                                                                 'WHERE id=?',
                                                                                                 (us_id, )).fetchone():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Изменить данные")
            button2 = types.KeyboardButton("Отписаться от рассылки")
            button3 = types.KeyboardButton("Меню")
            markup.add(button1, button2, button3)
            bot.send_message(message.chat.id, 'Вы уже подписаны на рассылку о погоде!', reply_markup=markup)

        elif message.text == 'Меню' and status_search == 0:
            markup = menu()
            bot.send_message(message.chat.id, 'Возвращаю вас в главное меню...', reply_markup=markup)

        elif status_search == 1:
            city_now = message.text
            markup = types.InlineKeyboardMarkup(row_width=2)
            button0 = types.InlineKeyboardButton("Сейчас", callback_data='-1')
            button = types.InlineKeyboardButton("Сегодня", callback_data='0')
            button1 = types.InlineKeyboardButton("Завтра", callback_data='1')
            button2 = types.InlineKeyboardButton("Послезавтра", callback_data='2')
            markup.add(button0, button, button1, button2)
            bot.send_message(message.chat.id, 'Выберите день, на который вы хотите узнать погоду:', reply_markup=markup)
            status_search = 0

        elif status_search == 2:
            city = message.text
            user = message.from_user.username
            us_id = message.from_user.id
            bot.send_message(message.chat.id, 'Выберите время, в которое вам будут приходить уведомления о погоде '
                                              '(в формате HH:MM):')
            status_search = 3

        elif status_search == 5:
            city = message.text
            user = message.from_user.username
            us_id = message.from_user.id
            bot.send_message(message.chat.id, 'Выберите время, в которое вам будут приходить уведомления о погоде '
                                              '(в формате HH:MM):')
            status_search = 4

        elif status_search == 3:
            us_time = message.text
            if is_valid_time(us_time):
                status_search = 0
                insert_into_db((us_id, user, city, us_time))
                bot.send_message(message.chat.id, 'Вы успешно подписались на рассылку о погоде в выбранном вами '
                                                  'регионе!')

            else:
                status_search = 3
                bot.send_message(message.chat.id,
                                 'Введите корректное время (в формате HH:MM):')

        elif status_search == 4:
            us_time = message.text
            if is_valid_time(us_time):
                status_search = 0
                update_db([city, us_time, us_id])
                bot.send_message(message.chat.id, 'Вы успешно обновили данные для рассылки о погоде в выбранном вами '
                                                  'регионе!')

            else:
                status_search = 4
                bot.send_message(message.chat.id,
                                 'Введите корректное время (в формате HH:MM):')
        else:
            bot.send_message(message.chat.id, 'Я не знаю что ответить 😢')



@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == '-1':
                bot.send_message(call.message.chat.id, get_weather(address_to_position(city_now), -1))
            elif call.data == '0':
                bot.send_message(call.message.chat.id, get_weather(address_to_position(city_now), 0))
            elif call.data == '1':
                bot.send_message(call.message.chat.id, get_weather(address_to_position(city_now), 1))
            elif call.data == '2':
                bot.send_message(call.message.chat.id, get_weather(address_to_position(city_now), 2))

            # remove inline buttons
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выберите день, на который вы хотите узнать погоду:", reply_markup=None)

    except Exception as e:
        print(repr(e))


# RUN
bot.polling(none_stop=True)
while True:
    schedule.run_pending()
    time.sleep(1)