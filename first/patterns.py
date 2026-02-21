import re
from datetime import datetime
import random


def handle_greeting(match=None):
    return "Здравствуйте! Чем могу помочь?"


def handle_farewell(match=None):
    return "До свидания! Хорошего дня!"


def handle_weather(match):
    city = match.group(1)
    return f"Погода в городе {city}: солнечно, +18°C (демо-режим)"


def handle_name(match, bot):
    bot.user_name = match.group(1)
    return f"Приятно познакомиться, {bot.user_name}!"


def handle_time(match=None):
    current_time = datetime.now().strftime("%H:%M")
    return f"Сейчас {current_time}"


def handle_date(match=None):
    current_date = datetime.now().strftime("%d.%m.%Y")
    return f"Сегодня {current_date}"

def handle_YES_NO(match=None):
    responses = [
        "Бесспорно", "Предрешено", "Никаких сомнений",
        "Определённо да", "Можешь быть уверен в этом",
        "Мне кажется - да", "Вероятнее всего", "Хорошие перспективы",
        "Знаки говорят - да", "Да",
        "Пока не ясно, попробуй снова", "Спроси позже",
        "Лучше не рассказывать", "Сейчас нельзя предсказать",
        "Сконцентрируйся и спроси опять",
        "Даже не думай", "Мой ответ - нет", "По моим данным - нет",
        "Перспективы не очень хорошие", "Весьма сомнительно"
    ]
    return random.choice(responses)

def handle_help(match=None):
    return """Я могу ответить на следующие запросы:
- Приветствие (привет, здравствуй, добрый день)
- Прощание (пока, до свидания)
- Погода в [город]
- Меня зовут [имя]
- Который час?
- Какая дата?
- Помощь
- Завтра идти на пары?
- Пока"""


patterns = [
    (re.compile(r"^(привет|здравствуй|добрый день|здравствуйте)$", re.IGNORECASE), handle_greeting),
    (re.compile(r"^(пока|до свидания|всего доброго)$", re.IGNORECASE), handle_farewell),
    (re.compile(r"погода в ([а-яА-Яa-zA-Z\- ]+)", re.IGNORECASE), handle_weather),
    (re.compile(r"меня зовут ([а-яА-Яa-zA-Z]+)", re.IGNORECASE), handle_name),
    (re.compile(r"(который час|сколько времени|время)", re.IGNORECASE), handle_time),
    (re.compile(r"(какая дата|какое сегодня число|дата)", re.IGNORECASE), handle_date),
    (re.compile(r"(помощь|что ты умеешь|помоги)", re.IGNORECASE), handle_help),
    (re.compile(r"(завтра идти на пары)", re.IGNORECASE, ), handle_YES_NO),
]
