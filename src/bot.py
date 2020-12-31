import ast
from os import getenv

import requests
import telebot
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv

import logs
import plotutil
from deadline import Deadline
from service import Service, ApiException
from util import search_dates, parse_time

load_dotenv(find_dotenv())
del load_dotenv, find_dotenv

TOKEN = getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
service = Service(getenv('API_SERVICE_URL'))
bot.skip_pending = True
logs.init(bot)

JOKES_URL = 'https://www.anekdot.ru/random/anekdot/'
HEADERS = {
    'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "I'm TimetableBot!\n.")


@bot.message_handler(commands=['total_deadlines_of_year_plot'])
def deadlines_per_month_plot(message):
    deadlines = service.get_deadlines(message.chat.id, relevant=False)
    if not deadlines:
        bot.send_message(message.chat.id, "Кажись дедлайнов нет")
        return
    plot = plotutil.get_plot_of_deadlines_per_month_of_year((it.dateTime for it in deadlines))
    bot.send_photo(message.chat.id, plot)


@bot.message_handler(commands=['total_deadlines_of_week_plot', 'week_plot'])
def deadlines_per_month_plot(message):
    deadlines = service.get_deadlines(message.chat.id, relevant='total' not in message.text)
    if not deadlines:
        bot.send_message(message.chat.id, "Кажись дедлайнов нет")
        return
    plot = plotutil.get_plot_of_deadlines_per_day_of_week((it.dateTime for it in deadlines))
    bot.send_photo(message.chat.id, plot)


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
            result = search_dates(input_date)
            if result is None:
                msg = bot.reply_to(message, 'Я не смог распознать дату, попробуйте еще раз!')
                bot.register_next_step_handler(msg, process_date_step)
                return
            else:
                deadline_time = result[0][1].strftime(getenv('SERVICE_DATETIME_FMT'))
                deadlines_dict[chat_id].dateTime = deadline_time
                bot.send_message(message.chat.id, f"Твой deadline: {deadlines_dict[chat_id].title}\n"
                                                  f"{str(deadlines_dict[chat_id].dateTime)}")
                service.post_deadline(Deadline(
                    creatorId=message.from_user.id,
                    groupId=message.chat.id,
                    title=deadlines_dict[chat_id].title,
                    dateTime=deadlines_dict[chat_id].dateTime
                ))
                del deadlines_dict[chat_id]
        except Exception:
            bot.reply_to(message, 'Ошибка!')

    text_to_parse = message.text.replace("/add", '').lstrip()
    if text_to_parse.startswith("/add" + getenv("BOT_NAME")):
        text_to_parse = text_to_parse.replace("/add" + getenv("BOT_NAME"), '')
    if message.chat.type == 'private' and text_to_parse == '':
        input_title(message)
    else:
        leadTimeBegin = text_to_parse.find('[')
        if leadTimeBegin != -1:
            leadTimeEnd = text_to_parse.rfind(']')
            lt = parse_time(text_to_parse[leadTimeBegin + 1: leadTimeEnd])
            text_to_parse = text_to_parse[:leadTimeBegin] + text_to_parse[leadTimeEnd + 1:]
        else:
            lt = None

        result = search_dates(text_to_parse)
        if result is None:
            msg = "Упс, ошибка!"
            bot.send_message(message.chat.id, msg)
        else:
            from datetime import datetime
            if len(result) > 1:
                result = list(result)
                result[0] = list(result[0])
                if result[0][1].year + result[0][1].month + result[0][1].day == 0:
                    result[0], result[1] = result[1], result[0]
                text_to_parse = text_to_parse.replace(result[1][0], '')
                result[0][1] = datetime.combine(result[0][1].date(), result[1][1].time())

            deadline_time = result[0][1]
            title = text_to_parse.replace(result[0][0], '')

            deadline_time = deadline_time.strftime(getenv('SERVICE_DATETIME_FMT'))
            res = Deadline(
                creatorId=message.from_user.id,
                groupId=message.chat.id,
                title=title,
                dateTime=deadline_time,
                leadTime=lt
            )
            deadline_id = service.post_deadline(res).id
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(
                text='Приоритет: средний', callback_data=str({'action': 'set_priority', 'id': deadline_id, 'value': 1}))
            )
            bot.send_message(message.chat.id, "Твой deadline: \n" + res.to_string(), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call: telebot.types.CallbackQuery):
    data = ast.literal_eval(call.data)
    if data['action'] == 'set_priority':
        service.patch_deadline(data['id'], {'priority': data['value']})
        markup = telebot.types.InlineKeyboardMarkup()
        new_p = data['value'] + 1
        if new_p > 1:
            new_p = -1
        p_text = {
            -1: 'высокий',
            0: 'средний',
            1: 'низкий'
        }[new_p]
        markup.add(telebot.types.InlineKeyboardButton(
            text='Приоритет: ' + p_text, callback_data=str({'action': 'set_priority', 'id': data['id'], 'value': new_p}))
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, call.inline_message_id, markup)


@bot.message_handler(func=lambda message: message.text and message.text.startswith('/del'))
def del_expense(message):
    """Удаляет одну запись о дедлайне по её идентификатору"""
    text = message.text.replace(getenv("BOT_NAME"), "")
    deadline_id = int(text[4:])

    try:
        service.delete_deadline(deadline_id, message.chat.id)
    except ApiException as e:
        if e.code == 417:
            msg = f"Ошибка! У вас не достаточно прав!"
        else:
            msg = f"Ошибка сервиса"
    else:
        msg = "Удалил ^-^"

    bot.reply_to(message, msg)


@bot.message_handler(commands=['deadlines'])
def send_deadlines(message):
    try:
        deadlines = service.get_deadlines(message.chat.id)
    except ApiException:
        msg = f"Ошибка сервиса"
        bot.reply_to(message, msg)
        return

    if not deadlines:
        bot.send_message(message.chat.id, "Кажись тут пусто")
    else:
        user_message = [
            f"{it.to_string()} \n"
            f"создатель: @{bot.get_chat_member(message.chat.id, it.creatorId).user.username}\n"
            f"/del{it.id} для удаления"
            for it in deadlines
        ]
        answer_message = "Текущие deadlines, о которых мне известно:\n\n" + "\n\n".join(user_message)
        bot.send_message(message.chat.id, answer_message)


@bot.message_handler(commands=['schedule'])
def send_deadlines(message):
    try:
        deadlines = service.get_schedule(message.chat.id)
    except ApiException as e:
        if e.code == 417:
            msg = 'всё не успеть('
        else:
            msg = "Ошибка сервиса"
        bot.reply_to(message, msg)
        return

    if not deadlines:
        bot.send_message(message.chat.id, "дедлайнов нет")
    else:
        user_message = [
            f"{it.title} завершить до {it.dateTime}"
            for it in deadlines
        ]
        answer_message = "Рекомендую следовать следующему расписанию:\n\n" + "\n\n".join(user_message)
        bot.send_message(message.chat.id, answer_message)


@bot.message_handler(commands=['joke'])
def send_joke(message):
    """
    рандомные шуточки в чат
    """
    r = requests.get(JOKES_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'lxml')
    joke_text = soup.find('div', {'class': 'topicbox', 'data-t': 'j'}).find('div', {'class': 'text'})
    for br in joke_text.find_all("br"):
        br.replace_with("\n" + br.text)
    bot.send_message(message.chat.id, joke_text.text)
