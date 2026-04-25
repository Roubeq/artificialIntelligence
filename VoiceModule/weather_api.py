import requests

API_KEY = "5c51662750ca6f7e4942723400e74b90"
BASE_URL = "http://api.weatherstack.com/current"


def get_weather(city):
    params = {
        "access_key": API_KEY,
        "query": city,
        "units": "m"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "error" in data:
            return f"Ошибка: {data['error']['info']}"

        if "current" in data:
            temp = data["current"]["temperature"]
            wind_speed = data["current"]["wind_speed"]
            weather_desc = data["current"]["weather_descriptions"][0] if data["current"][
                "weather_descriptions"] else "без осадков"
            humidity = data["current"]["humidity"]

            return (f"Погода в городе {city}:\n"
                    f"🌡 Температура: {temp}°C\n"
                    f"💨 Ветер: {wind_speed} м/с\n"
                    f"☁️ Описание: {weather_desc}\n"
                    f"💧 Влажность: {humidity}%")
        else:
            return "Не удалось получить данные о погоде. Проверьте название города."

    except Exception as e:
        return f"Ошибка при получении погоды: {str(e)}"
