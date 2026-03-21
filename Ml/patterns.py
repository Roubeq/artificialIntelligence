# patterns.py (только измененные части)
import re
from datetime import datetime, timedelta
import random
from weather_api import get_weather
from database import save_user, get_user_id_by_name, log_weather_query
import spacy

try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    print("Модель ru_core_news_sm не найдена. Установите: python -m spacy download ru_core_news_sm")
    nlp = None


def extract_city_with_spacy(text):
    if nlp is None:
        return None

    doc = nlp(text)
    cities = []

    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"]:
            cities.append(ent.lemma_)

    if not cities:
        for token in doc:
            if token.ent_type_ in ["LOC", "GPE"]:
                cities.append(token.lemma_)

    return cities[0] if cities else None


def extract_date_from_text(text):
    text_lower = text.lower()
    today = datetime.now().date()

    date_patterns = {
        'сегодня': today,
        'завтра': today + timedelta(days=1),
        'послезавтра': today + timedelta(days=2),
        'вчера': today - timedelta(days=1),
        'позавчера': today - timedelta(days=2),
    }

    for date_word, date_value in date_patterns.items():
        if date_word in text_lower:
            return date_value, date_word

    weekdays = {
        'понедельник': 0, 'пн': 0,
        'вторник': 1, 'вт': 1,
        'среду': 2, 'среда': 2, 'ср': 2,
        'четверг': 3, 'чт': 3,
        'пятницу': 4, 'пятница': 4, 'пт': 4,
        'субботу': 5, 'суббота': 5, 'сб': 5,
        'воскресенье': 6, 'вс': 6,
    }

    for day_name, day_num in weekdays.items():
        if day_name in text_lower:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_day = today + timedelta(days=days_ahead)
            return next_day, day_name

    return today, "сегодня"


def handle_greeting(match=None, user_id=None):
    return "Здравствуйте! Чем могу помочь?"


def handle_farewell(match=None, user_id=None):
    return "До свидания! Хорошего дня!"


def handle_weather_simple(match, user_id=None):
    if isinstance(match, str):
        text = match
    elif hasattr(match, 'string'):
        text = match.string
    else:
        text = str(match)

    print(f"\n🌤 Обработка запроса погоды: '{text}'")

    if nlp is None:
        return "Ошибка: spaCy не загружен. Не могу определить город."

    city = extract_city_with_spacy(text)

    if not city:
        return "Пожалуйста, укажите город. Например: 'Какая погода в Москве?' или 'Сколько градусов в Питере?'"

    target_date, date_desc = extract_date_from_text(text)
    today = datetime.now().date()

    if target_date < today:
        return f"❌ Извините, я могу показать погоду только на сегодня и будущие даты. Вы спросили про {date_desc}."
    elif target_date > today + timedelta(days=7):
        return f"❌ Извините, прогноз доступен только на 7 дней вперед. Вы спросили на {date_desc}."

    print(f"  🌆 Запрашиваю погоду для города: {city}, дата: {date_desc}")
    weather_info = get_weather(city)

    try:
        temp_match = re.search(r'Температура:\s*([-+]?\d+)', weather_info)
        wind_match = re.search(r'Ветер:\s*([\d.]+)', weather_info)

        if temp_match and wind_match and user_id:
            temperature = float(temp_match.group(1))
            wind_speed = float(wind_match.group(1))
            log_weather_query(user_id, city, temperature, wind_speed)
    except Exception as e:
        print(f"Ошибка при логировании погоды: {e}")

    if date_desc != "сегодня":
        weather_info = f"📅 {date_desc.capitalize()}:\n" + weather_info

    return weather_info


def handle_name(match, bot, user_id=None):
    user_name = match.group(1)
    bot.user_name = user_name
    user_id = save_user(user_name)
    bot.user_id = user_id
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
- Погода (например: "Какая погода в Москве?" или просто "Какая погода?")
- Меня зовут [имя]
- Который час?
- Какая дата?
- Моя статистика
- Завтра идти на пары?
- Помощь

Также я поддерживаю диалог: если спросить "Какая погода?" без города,
я уточню город в следующем сообщении."""


def handle_stats(match=None, user_id=None):
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
    (re.compile(r"меня зовут ([а-яА-Яa-zA-Z]+)", re.IGNORECASE), handle_name),
    (re.compile(r"(который час|сколько времени|время)", re.IGNORECASE), handle_time),
    (re.compile(r"(какая дата|какое сегодня число|дата)", re.IGNORECASE), handle_date),
    (re.compile(r"(помощь|что ты умеешь|помоги)", re.IGNORECASE), handle_help),
    (re.compile(r"(завтра идти на пары)", re.IGNORECASE), handle_YES_NO),
    (re.compile(r"(моя статистика|статистика)", re.IGNORECASE), handle_stats),
]