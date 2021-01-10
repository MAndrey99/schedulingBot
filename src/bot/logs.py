from logging import *
from os import getenv
from sys import stdout

from telebot import TeleBot

initialized = False


class TelegramMessageHandler(NullHandler):
    def __init__(self, bot: TeleBot, level):
        super().__init__(level)
        self.bot = bot

    def handle(self, record: LogRecord):
        message = f"Оповещение о{'б' if record.levelno == ERROR else ' критической'} ошибке:\n{self.format(record)}"
        self.bot.send_message(getenv('ADMIN_ID'), message)


def init(bot: TeleBot):
    """
    Функция проводит первоначальную настройку логгера. Задает формат, уровень, потоки, фильтры и тд...
    """
    global initialized
    assert not initialized
    initialized = True

    root_logger = getLogger()
    root_logger.setLevel(INFO)

    # добавляем вывод в консоль
    print_handler = StreamHandler(stdout)
    print_handler.setFormatter(
        Formatter("%(asctime)s [%(levelname)s] module:'%(module)s' line:%(lineno)s - %(message)s",
                  datefmt='%m.%d.%Y %H:%M:%S')
    )
    root_logger.addHandler(print_handler)

    # добавляем TelegramMessageHandler
    message_handler = TelegramMessageHandler(bot, level=ERROR)
    message_handler.setFormatter(Formatter("module:'%(module)s' line:%(lineno)s - %(message)s"))
    root_logger.addHandler(message_handler)
