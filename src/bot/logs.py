from logging import *
from os import getenv
from sys import stdout

from telebot import TeleBot

initialized = False


class CloneFilter(Filter):
    def __init__(self):
        super().__init__()
        self.lastRecords: list[LogRecord] = []

    def filter(self, record: LogRecord):
        if record.levelno > INFO:  # только серьёздные ошибки можно пропускать чтобы облегчить логи!
            return True

        # проверяем было ли подобное исключение и очищаем старые из истории
        i = 0
        while i < len(self.lastRecords):
            it = self.lastRecords[i]

            if record.created - it.created > 20:
                del self.lastRecords[i]  # очищаем старую ошибку
                continue

            if (record.lineno, record.module) == (it.lineno, it.module) and record.msg[:15] == it.msg[:15]:
                debug(f"Возникло исключение, эквиволентное тому, что было {record.created - it.created:.1f} "
                      f"секунд назад")
                self.lastRecords[i] = record  # вместо старого кладем эквивалентное новое
                return False

            i += 1

        self.lastRecords.append(record)
        return True


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
    root_logger.addFilter(CloneFilter())

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
