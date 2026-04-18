import random


def greeting_skill():
    responses = [
        "Здравствуйте! Чем могу помочь?",
        "Привет! Как я могу вам помочь?",
        "Добрый день! Чем могу быть полезен?",
        "Приветствую! Задавайте вопросы.",
    ]
    return random.choice(responses)
