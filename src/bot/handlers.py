from datetime import datetime
from os import getenv

from src.bot.bot import bot, inlineKeyboardManager
from src.bot.deadline import Deadline
from src.bot.inlineKeyboardManager import InlineKeyboardManager
from src.bot.service import service, ApiException
from src.bot.util import search_dates, parse_time


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
            res = service.post_deadline(res)
            markup = InlineKeyboardManager.get_markup_for_deadline(res)
            bot.send_message(message.chat.id, "Твой deadline: \n" + res.to_string(), reply_markup=markup)


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
            f"{it.to_string()}\n"
            f"создатель: @{bot.get_chat_member(message.chat.id, it.creatorId).user.username}"
            for it in deadlines
        ]
        answer_message = "Текущие deadlines, о которых мне известно:\n\n" + "\n\n".join(user_message)
        bot.send_message(message.chat.id, answer_message, reply_markup=inlineKeyboardManager.get_markup_for_deadlines(
            deadlines
        ))


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