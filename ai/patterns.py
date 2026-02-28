import re
from datetime import datetime
import random
from weather_api import get_weather
from database import save_user, get_user_id_by_name

def handle_greeting(match=None, user_id=None):
    return "Здравствуйте! Чем могу помочь?"

def handle_farewell(match=None, user_id=None):
    return "До свидания! Хорошего дня!"

def handle_weather(match, user_id=None):
    city = match.group(1).strip()
    weather_info = get_weather(city)
    return weather_info

def handle_name(match, bot, user_id=None):
    user_name = match.group(1)
    bot.user_name = user_name
    # Сохраняем пользователя в базу данных
    save_user(user_name)
    return f"Приятно познакомиться, {user_name}!"

def handle_time(match=None, user_id=None):
    current_time = datetime.now().strftime("%H:%M")
    return f"Сейчас {current_time}"

def handle_date(match=None, user_id=None):
    current_date = datetime.now().strftime("%d.%m.%Y")
    return f"Сегодня {current_date}"

def handle_YES_NO(match=None, user_id=None):
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

def handle_help(match=None, user_id=None):
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

def handle_stats(match=None, user_id=None):
    """Обработка запроса статистики"""
    from database import get_user_stats
    if user_id:
        stats = get_user_stats(user_id)
        if stats:
            return (f"📊 Ваша статистика:\n"
                   f"Имя: {stats['name']}\n"
                   f"Первый визит: {stats['first_seen']}\n"
                   f"Последний визит: {stats['last_seen']}\n"
                   f"Всего сообщений: {stats['messages_count']}\n"
                   f"Запросов погоды: {stats['weather_queries']}")
    return "Статистика недоступна"

patterns = [
    (re.compile(r"^(привет|здравствуй|добрый день|здравствуйте)$", re.IGNORECASE), handle_greeting),
    (re.compile(r"^(пока|до свидания|всего доброго)$", re.IGNORECASE), handle_farewell),
    (re.compile(r"погода в ([а-яА-Яa-zA-Z\- ]+)", re.IGNORECASE), handle_weather),
    (re.compile(r"меня зовут ([а-яА-Яa-zA-Z]+)", re.IGNORECASE), handle_name),
    (re.compile(r"(который час|сколько времени|время)", re.IGNORECASE), handle_time),
    (re.compile(r"(какая дата|какое сегодня число|дата)", re.IGNORECASE), handle_date),
    (re.compile(r"(помощь|что ты умеешь|помоги)", re.IGNORECASE), handle_help),
    (re.compile(r"(завтра идти на пары)", re.IGNORECASE), handle_YES_NO),
    (re.compile(r"(моя статистика|статистика)", re.IGNORECASE), handle_stats),
]