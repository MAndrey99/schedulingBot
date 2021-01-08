import re
from datetime import datetime, date, time
from typing import *
from io import StringIO

from dateparser import search

time_reg = re.compile(r'(?P<hours>\d{1,2}(?:\.\d+)?)(?::(?P<minutes>\d{1,2})(?::(?P<seconds>\d{1,2}))?)?')
digit_dates_symbols = set('0123456789-/.: []')


def search_dates(text: str):
    def delete_digits_in_words(s: str) -> str:
        res = StringIO()
        word_begin = -1
        digit_begin = -1
        ignore_space = True

        for n, it in enumerate(s):
            if it == ' ':
                for beg in (word_begin, digit_begin):
                    if beg >= 0:
                        res.write(s[beg: n])
                        ignore_space = False
                        break
                word_begin = digit_begin = -1
            elif it in digit_dates_symbols:
                if word_begin >= 0:
                    res.write(s[word_begin:n])
                    ignore_space = False
                    word_begin = -1
                elif digit_begin < 0:
                    digit_begin = n
            else:
                digit_begin = -1
                if word_begin < 0:
                    word_begin = n

            if not ignore_space:
                res.write(' ')
                ignore_space = True

        for beg in (word_begin, digit_begin):
            if beg >= 0:
                res.write(s[beg:])
                break

        return res.getvalue().rstrip()

    text = delete_digits_in_words(text)
    r1 = search.search_dates(''.join(filter(lambda it: it in digit_dates_symbols, text)), languages=['de'], settings={
        'DATE_ORDER': 'DMY'
    }) or {}
    r2 = search.search_dates(text, languages=['ru', 'en'], settings={
        'TIMEZONE': 'Europe/Moscow',
        'RELATIVE_BASE': datetime.combine(date.today(), time(23, 59, 0)),
        'PREFER_DATES_FROM': 'future',
        'DATE_ORDER': 'DMY'
    }) or {}

    if r2:
        # убираем из r2 записи которые входят в r1
        r2 = set(filter(lambda it2: all(map(lambda it1: it1[0].find(it2[0]) == -1, r1)), r2))

    return list(set(r1) | set(r2))


def parse_time(text: str) -> Optional[int]:
    """
    :param text: строка формата hh:mm:ss
    :return: количество секунд
    """
    m = time_reg.match(text)
    if m:
        seconds = m.group('seconds')
        minutes = m.group('minutes')
        return (int(seconds) if seconds else 0) \
               + (int(minutes) if minutes else 0)*60 \
               + int(float(m.group('hours'))*60*60)
    else:
        return None


def seconds_to_time_str(secs: int) -> str:
    hours = secs // (60*60)
    secs -= hours * (60*60)
    minutes = secs // 60
    secs -= minutes * 60
    return f'{hours:0>2}:{minutes:0>2}:{secs:0>2}'
