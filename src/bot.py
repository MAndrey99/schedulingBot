import json
from datetime import *
from os import getenv

import bs4
import requests
import telebot
from dateparser import search
from dotenv import load_dotenv, find_dotenv

import logs
import plotutil
from deadline import Deadline

load_dotenv(find_dotenv())
del load_dotenv, find_dotenv

SERVICE_DATETIME_FMT = "%d-%m-%Y %H:%M:%S"
TOKEN = getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
bot.skip_pending = True
logs.init(bot)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "I'm TimetableBot!\n.")


@bot.message_handler(commands=['deadlines_per_month_plot'])
def deadlines_per_month_plot(message):
    response = requests.get(getenv('API_SERVICE_URL') + "deadlines", params={'relevant': False, 'groupId': message.chat.id})
    if response.status_code != 200:
        bot.send_message(message.chat.id, "Ошибка сервера: " + str(response.status_code))
    else:
        data = json.loads(response.text)
        if data["deadlines"] is None:
            bot.send_message(message.chat.id, "Кажись дедлайнов нет")
        try:
            plot = plotutil.get_plot_of_deadlines_per_month_of_year(
                (datetime.strptime(it["dateTime"], SERVICE_DATETIME_FMT) for it in data["deadlines"])
            )

            bot.send_photo(message.chat.id, plot)
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка(")
            logs.error(e)


@bot.message_handler(commands=['deadlines_per_day_of_week_plot'])
def deadlines_per_month_plot(message):
    response = requests.get(getenv('API_SERVICE_URL') + "deadlines", params={'relevant': False, 'groupId': message.chat.id})
    if response.status_code != 200:
        bot.send_message(message.chat.id, "Ошибка сервера: " + str(response.status_code))
    else:
        data = json.loads(response.text)
        if data["deadlines"] is None:
            bot.send_message(message.chat.id, "Кажись дедлайнов нет")
        try:
            plot = plotutil.get_plot_of_deadlines_per_day_of_week(
                (datetime.strptime(it["dateTime"], SERVICE_DATETIME_FMT) for it in data["deadlines"])
            )

            bot.send_photo(message.chat.id, plot)
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка(")
            logs.error(e)


@bot.message_handler(commands=['charlie_hebdo'])
def send_photo(message):
    url = 'https://www.anekdot.ru/random/caricatures/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    r = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')  # Создаем сам объект , передаем в него наш код страницы (html)

    img_src = soup.find('div', {'class': 'topicbox', 'data-t': 'e'}).find('div', {'class': 'text'}).find('img')['src']
    title = soup.find('div', {'class': 'topicbox', 'data-t': 'e'}).find('div', {'class': 'text'}).text
    bot.send_photo(message.chat.id, img_src, caption=title)


@bot.message_handler(commands=['add'])
def add_deadline(message):
    deadlines_dict = {}

    def input_title(message):
        msg = bot.reply_to(message, 'Введи заголовок дедлайна:')
        bot.register_next_step_handler(msg, process_title_step)

    def process_title_step(message):
        try:
            chat_id = message.chat.id
            title = message.text
            deadline = Deadline(title)
            deadlines_dict[chat_id] = deadline
            msg = bot.reply_to(message, 'Дата и/или время:')
            bot.register_next_step_handler(msg, process_date_step)
        except Exception:
            bot.reply_to(message, 'Ошибка!')

    def process_date_step(message):
        try:
            chat_id = message.chat.id
            input_date = message.text
            result = search.search_dates(input_date, ['ru'], settings={
                'TIMEZONE': 'Europe/Moscow',
                'RELATIVE_BASE': datetime.combine(date.today(), time(23, 59, 0)), 'PREFER_DATES_FROM': 'future'
            })
            if result is None:
                msg = bot.reply_to(message, 'Я не смог распознать дату, попробуйте еще раз!')
                bot.register_next_step_handler(msg, process_date_step)
                return
            else:
                deadline_time = result[0][1].strftime(SERVICE_DATETIME_FMT)
                deadlines_dict[chat_id].dateTime = deadline_time
                bot.send_message(message.chat.id, f"Твой deadline: {deadlines_dict[chat_id].title}\n"
                                                  f"{str(deadlines_dict[chat_id].dateTime)}")
                data = {
                    "creatorId": message.from_user.id,
                    "groupId": message.chat.id,
                    "title": deadlines_dict[chat_id].title,
                    "dateTime": deadlines_dict[chat_id].dateTime,
                    "description": "tmp description"
                }
                post_data = json.dumps(data)
                del deadlines_dict[chat_id]
                requests.post(url=getenv('API_SERVICE_URL') + "deadlines", data=post_data)
        except Exception:
            bot.reply_to(message, 'Ошибка!')

    text_to_parse = message.text
    if text_to_parse.startswith("/add"):
        text_to_parse = text_to_parse.replace("/add", '')
    if text_to_parse.startswith("/add@Timetables_bot"):
        text_to_parse = text_to_parse.replace("/add@Timetables_bot", '')
    if message.chat.type == 'private' and text_to_parse == '':
        input_title(message)
    else:
        result = search.search_dates(text_to_parse, ['ru'], settings={'TIMEZONE': 'Europe/Moscow',
                                                                      'RELATIVE_BASE': datetime.combine(date.today(),
                                                                        time(23, 59, 0)),
                                                                      'PREFER_DATES_FROM': 'future'})
        if result is None:
            msg = "Упс, ошибка!"
            bot.send_message(message.chat.id, msg)
        else:
            substring = result[0][0]
            deadline_time = result[0][1]
            title = text_to_parse.replace(substring, '')
            deadline_time = deadline_time.strftime(SERVICE_DATETIME_FMT)
            bot.send_message(message.chat.id, "Твой deadline: " + title + '\n' + str(deadline_time))
            data = {
                "creatorId": message.from_user.id,
                "groupId": message.chat.id,
                "title": title,
                "dateTime": deadline_time,
                "description": "tmp description"
            }
            post_data = json.dumps(data)
            requests.post(url=getenv('API_SERVICE_URL')+"deadlines", data=post_data)


@bot.message_handler(func=lambda message: message.text and message.text.startswith('/del'))
def del_expense(message):
    """Удаляет одну запись о дедлайне по её идентификатору"""
    text = message.text.replace("@" + getenv("BOT_NAME"), "")
    deadline_id = int(text[4:])
    responce = requests.delete(url=getenv('API_SERVICE_URL') + "deadlines", params={'id': deadline_id, 'groupId': message.chat.id})

    if responce.status_code == 200:
        msg = "Удалил ^-^"
        bot.reply_to(message, msg)
    elif responce.status_code == 417:
        msg = f"Ошибка! У вас не достаточно прав!"
        bot.reply_to(message, msg)
    else:
        msg = f"Ошибка сервиса: {responce.status_code}"
        bot.reply_to(message, msg)


@bot.message_handler(commands=['deadlines'])
def send_deadlines(message):
    response = requests.get(getenv('API_SERVICE_URL')+"deadlines", params={'groupId': message.chat.id})
    if response.status_code != 200:
        bot.send_message(message.chat.id, "Ошибка сервиса: " + str(response.status_code))
    else:
        data = json.loads(response.text)
        if data["deadlines"] is None:
            bot.send_message(message.chat.id, "Кажись тут пусто")
        else:
            user_message = [
                f"{deadlines['title']}: {deadlines['dateTime']} \n"
                f"создатель: @{bot.get_chat_member(message.chat.id, deadlines['creatorId']).user.username}\n"
                f"/del{deadlines['id']} для удаления"
                for deadlines in data["deadlines"]]
            answer_message = "Текущие deadlines, о которых мне известно:\n\n" + "\n\n".join(user_message)
            bot.send_message(message.chat.id, answer_message)
