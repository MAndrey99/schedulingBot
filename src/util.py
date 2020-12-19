import re
from datetime import datetime, date, time
from typing import *

from dateparser import search

time_reg = re.compile(r'(?P<hours>\d{1,2}(?:\.\d+)?)(?:(?P<minutes>\d{1,2})(?:(?P<seconds>\d{1,2}))?)?')


def search_dates(text: str):
    return search.search_dates(text.replace('-', '/'), ['ru'], settings={
        'TIMEZONE': 'Europe/Moscow',
        'RELATIVE_BASE': datetime.combine(date.today(), time(23, 59, 0)),
        'PREFER_DATES_FROM': 'future'
    })


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
