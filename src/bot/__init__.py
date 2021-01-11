from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
del load_dotenv, find_dotenv

import src.bot.logs as logs
import src.bot.handlers
import src.bot.plot_handlers
import src.bot.additional_handlers
from src.bot.bot import bot, TOKEN
from src.bot import database

logs.init(bot)
database.init()
