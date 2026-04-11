# expand_dataset.py
import pandas as pd

# Загружаем существующий датасет
df = pd.read_csv("dataset.csv")

# Удаляем мусор
df = df[~df['intent'].isin(['farewall', 'intent'])]
df = df.drop_duplicates(subset=['text'])

# НОВЫЕ ПРИМЕРЫ ДЛЯ ПОГОДЫ (weather - с городом)
new_weather = [
    # Осадки
    ("что завтра по осадкам", "weather"),
    ("какие осадки ожидаются", "weather"),
    ("будет дождь или снег", "weather"),
    ("осадки в москве", "weather"),
    ("когда перестанет идти дождь", "weather"),
    ("сильные ли осадки", "weather"),
    ("дождь будет идти", "weather"),
    ("снег пойдет", "weather"),
    ("град ожидается", "weather"),
    ("ливень будет", "weather"),

    # Ветер
    ("сильный ветер сегодня", "weather"),
    ("какой ветер в питере", "weather"),
    ("ветрено на улице", "weather"),
    ("скорость ветра какая", "weather"),
    ("порывы ветра будут", "weather"),

    # Температура с разными формулировками
    ("сколько градусов тепла", "weather"),
    ("какая температура воздуха", "weather"),
    ("тепло или холодно", "weather"),
    ("мороз сильный", "weather"),
    ("жара какая", "weather"),
    ("прохладно на улице", "weather"),

    # Погода в разных городах
    ("погодка в новосибирске", "weather"),
    ("как погода в сочи", "weather"),
    ("что с погодой в екатеринбурге", "weather"),
    ("температура в нижнем новгороде", "weather"),
    ("владивосток погодные условия", "weather"),
    ("калининград градусы", "weather"),
    ("иркутск погода сегодня", "weather"),
    ("хабаровск температура", "weather"),
    ("краснодар погодка", "weather"),

    # Время
    ("погода на выходные", "weather"),
    ("какой прогноз на понедельник", "weather"),
    ("температура во вторник", "weather"),
    ("погода на следующей неделе", "weather"),
    ("на завтра что обещают", "weather"),
    ("послезавтра погода", "weather"),

    # Общие погодные вопросы
    ("солнечно будет", "weather"),
    ("пасмурно или ясно", "weather"),
    ("облачность какая", "weather"),
    ("туман утром будет", "weather"),
    ("гроза ожидается", "weather"),
    ("молния будет", "weather"),
    ("гололед на дорогах", "weather"),
    ("давление атмосферное", "weather"),
    ("влажность воздуха", "weather"),
]

# НОВЫЕ ПРИМЕРЫ ДЛЯ ПОГОДЫ БЕЗ ГОРОДА (weather_city_only)
new_weather_city_only = [
    ("что с осадками", "weather_city_only"),
    ("дождь будет", "weather_city_only"),
    ("снег ожидается", "weather_city_only"),
    ("ветер какой", "weather_city_only"),
    ("температура на улице", "weather_city_only"),
    ("сколько градусов", "weather_city_only"),
    ("какая погодка", "weather_city_only"),
    ("что там на улице", "weather_city_only"),
    ("холодно или жарко", "weather_city_only"),
    ("осадки какие", "weather_city_only"),
    ("солнце есть", "weather_city_only"),
    ("облачно или нет", "weather_city_only"),
    ("туман видно", "weather_city_only"),
    ("ветер дует", "weather_city_only"),
    ("тепло на улице", "weather_city_only"),
    ("прохладно сегодня", "weather_city_only"),
    ("мороз на улице", "weather_city_only"),
    ("жара какая", "weather_city_only"),
    ("давление как", "weather_city_only"),
    ("влажность какая", "weather_city_only"),
]

# НОВЫЕ ПРИМЕРЫ ДЛЯ yes_no (чтобы не путались с погодой)
new_yes_no = [
    ("стоит ли брать зонт", "yes_no"),
    ("нужен ли зонт", "yes_no"),
    ("брать зонт или нет", "yes_no"),
    ("одеваться тепло", "yes_no"),
    ("шапку надевать", "yes_no"),
    ("куртку брать", "yes_no"),
]

# НОВЫЕ ПРИМЕРЫ ДЛЯ UNKNOWN
new_unknown = [
    ("как работает нейросеть", "unknown"),
    ("что такое трансформеры", "unknown"),
    ("как учить python", "unknown"),
    ("где купить квартиру", "unknown"),
    ("лучший фильм 2024", "unknown"),
    ("как похудеть быстро", "unknown"),
    ("что такое любовь", "unknown"),
]

# ДОБАВЛЯЕМ
new_rows = []
new_rows.extend(new_weather)
new_rows.extend(new_weather_city_only)
new_rows.extend(new_yes_no)
new_rows.extend(new_unknown)

new_df = pd.DataFrame(new_rows, columns=["text", "intent"])
df = pd.concat([df, new_df], ignore_index=True)

# Удаляем дубликаты
df = df.drop_duplicates(subset=['text'])

# Перемешиваем
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Сохраняем
df.to_csv("dataset.csv", index=False)

print(f"✅ Датасет расширен!")
print(f"Всего записей: {len(df)}")
print(f"\nРаспределение по интентам:")
print(df['intent'].value_counts())

# Покажем примеры новых погодных фраз
print(f"\n🌤 Примеры новых погодных фраз:")
weather_examples = df[df['intent'] == 'weather'].tail(10)
for _, row in weather_examples.iterrows():
    print(f"  - {row['text']}")