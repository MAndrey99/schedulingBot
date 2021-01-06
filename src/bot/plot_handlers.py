import src.bot.plotutil as plotutil
from src.bot.service import service
from src.bot.bot import bot


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
