from datetime import *
from os import getenv

import telebot
from dateparser import search
from dotenv import load_dotenv, find_dotenv

import logs
import plotutil
from deadline import Deadline
from service import Service, ApiException

load_dotenv(find_dotenv())
del load_dotenv, find_dotenv

TOKEN = getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
service = Service(getenv('API_SERVICE_URL'))
bot.skip_pending = True
logs.init(bot)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "I'm TimetableBot!\n.")


@bot.message_handler(commands=['deadlines_per_month_plot'])
def deadlines_per_month_plot(message):
    deadlines = service.get_deadlines(message.chat.id, relevant=False)
    if not deadlines:
        bot.send_message(message.chat.id, "Кажись дедлайнов нет")
        return
    plot = plotutil.get_plot_of_deadlines_per_month_of_year((it.dateTime for it in deadlines))
    bot.send_photo(message.chat.id, plot)


@bot.message_handler(commands=['deadlines_per_day_of_week_plot'])
def deadlines_per_month_plot(message):
    deadlines = service.get_deadlines(message.chat.id, relevant=False)
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
            result = search.search_dates(input_date, ['ru'], settings={
                'TIMEZONE': 'Europe/Moscow',
                'RELATIVE_BASE': datetime.combine(date.today(), time(23, 59, 0)), 'PREFER_DATES_FROM': 'future'
            })
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

    text_to_parse = message.text
    if text_to_parse.startswith("/add"):
        text_to_parse = text_to_parse.replace("/add", '')
    if text_to_parse.startswith("/add" + getenv("BOT_NAME")):
        text_to_parse = text_to_parse.replace("/add" + getenv("BOT_NAME"), '')
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
            deadline_time = deadline_time.strftime(getenv('SERVICE_DATETIME_FMT'))
            bot.send_message(message.chat.id, "Твой deadline: " + title + '\n' + str(deadline_time))
            service.post_deadline(Deadline(
                creatorId=message.from_user.id,
                groupId=message.chat.id,
                title=title,
                dateTime=deadline_time
            ))


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
            f"{it.title}: {it.dateTime} \n"
            f"создатель: @{bot.get_chat_member(message.chat.id, it.creatorId).user.username}\n"
            f"/del{it.id} для удаления"
            for it in deadlines]
        answer_message = "Текущие deadlines, о которых мне известно:\n\n" + "\n\n".join(user_message)
        bot.send_message(message.chat.id, answer_message)
