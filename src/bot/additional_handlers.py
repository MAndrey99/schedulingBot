import requests
from bs4 import BeautifulSoup

from src.bot.bot import bot

JOKES_URL = 'https://www.anekdot.ru/random/anekdot/'
HEADERS = {
    'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Это тестовая версия, помощи не жди!")


@bot.message_handler(commands=['joke'])
def send_joke(message):
    """
    рандомные шуточки в чат
    """
    r = requests.get(JOKES_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'lxml')
    joke_text = soup.find('div', {'class': 'topicbox', 'data-t': 'j'}).find('div', {'class': 'text'})
    for br in joke_text.find_all("br"):
        br.replace_with("\n" + br.text)
    bot.send_message(message.chat.id, joke_text.text)
