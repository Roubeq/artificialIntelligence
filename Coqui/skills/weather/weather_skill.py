from dialog_manager import DialogState, dialog_manager
from patterns import extract_city_with_spacy
from weather_api import get_weather


def weather_skill(text: str, user_id: int, intent: str = "weather"):
    city = extract_city_with_spacy(text) if intent == "weather" else None
    if city:
        return get_weather(city)
    dialog_manager.set_state(user_id, DialogState.WAIT_CITY)
    return "В каком городе вас интересует погода?"
