from logging import *
from os import getenv
from sys import stdout

from telebot import TeleBot


def init(bot: TeleBot):
    """
    Функция проводит первоначальную настройку логгера. Задает формат, уровень, потоки, фильтры и тд...
    """
    formatter = Formatter("%(asctime)s [%(levelname)s] module:'%(module)s' line:%(lineno)s - %(message)s",
                          datefmt='%m.%d.%Y %H:%M:%S')  # определяем формат записей журнала

    root_logger = getLogger()  # главный логгер. В него все хэнлеры пихаем

    # добавляем вывод в консоль
    print_handler = StreamHandler(stdout)
    print_handler.setFormatter(formatter)
    root_logger.addHandler(print_handler)

    root_logger.setLevel(INFO)

    # далее создаем фильтер, чтобы, например, не кидать много ошибок о том, что сеть не доступна
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
    root_logger.addFilter(CloneFilter())

    # определяем свой хэндлер для отправки ошибок админу
    class MessageHandler(NullHandler):
        def handle(self, record: LogRecord):
            message = f"Оповещение о{'б' if record.levelno == ERROR else ' критической'} ошибке:\n{self.format(record)}"
            bot.send_message(getenv('ADMIN_ID'), message)

    # Определяем формат сообщений об ошибках(время не надо тк телеграмм сам его выводит)
    message_formatter = Formatter("module:'%(module)s' line:%(lineno)s - %(message)s")

    # добавляем MessageHandler
    message_handler = MessageHandler(level=ERROR)
    message_handler.setFormatter(message_formatter)
    root_logger.addHandler(message_handler)
