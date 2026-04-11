from datetime import datetime


def time_skill():
    return f"⌚ Сейчас {datetime.now().strftime('%H:%M')}"


def date_skill():
    return f"📅 Сегодня {datetime.now().strftime('%d.%m.%Y')}"
