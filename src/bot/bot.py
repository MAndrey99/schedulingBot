from os import getenv

import telebot

from src.bot.inlineKeyboardManager import InlineKeyboardManager
from src.bot.service import service

TOKEN = getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
bot.skip_pending = True

inlineKeyboardManager = InlineKeyboardManager(bot, service)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call: telebot.types.CallbackQuery):
    inlineKeyboardManager.handle_query(call)
