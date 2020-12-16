import os
import telebot
from flask import Flask, request
from bot import bot, TOKEN

server = Flask(__name__)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    print('new message')
    return "!", 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://timetables-bot.herokuapp.com/" + TOKEN)
    return "Hello from Heroku!", 200


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
