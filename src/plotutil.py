from datetime import datetime
from io import BytesIO
from typing import *

import numpy as np
from matplotlib import pyplot as plt

MONTHS = ("январь", "февраль", "март", "апрель", "май", "июнь",
          "июль", "август", "сенябрь", "октябрь", "ноябрь", "декабрь")  # месяца по порядку

WEEK_DAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


def get_plot_of_deadlines_per_month_of_year(deadlines_iter: Iterable[datetime.date]) -> BytesIO:
    num_of_deadlines = [0 for _ in range(12)]  # Ось Y графика
    max_y = 0

    for i in deadlines_iter:
        num_of_deadlines[i.month - 1] += 1
        max_y = max(num_of_deadlines[i.month - 1], max_y)

    plt.figure(figsize=(9, 6))
    plt.yticks(np.arange(0, max_y + 1, max(max_y // 10, 1)))
    plt.plot(MONTHS, num_of_deadlines)
    plt.grid()
    plt.xticks(rotation=30)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    return buf


def get_plot_of_deadlines_per_day_of_week(deadlines_iter: Iterable[datetime.date]) -> BytesIO:
    num_of_deadlines = [0 for _ in range(7)]  # Ось Y графика
    max_y = 0
    
    for i in deadlines_iter:
        num_of_deadlines[i.weekday()] += 1
        max_y = max(num_of_deadlines[i.weekday()], max_y)

    plt.figure(figsize=(9, 6))
    plt.yticks(np.arange(0, max_y + 1, max(max_y // 10, 1)))
    plt.bar(WEEK_DAYS, num_of_deadlines)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    return buf
