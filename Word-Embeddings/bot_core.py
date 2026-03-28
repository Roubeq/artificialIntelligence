import re
import random
from patterns import patterns
from database import init_db, log_message_to_db, save_user, get_user_id_by_name, get_last_user_state
from dialog_manager import dialog_manager, DialogState
from intent_classifier import get_intent_classifier


class ChatBot:
    def __init__(self):
        init_db()
        self.patterns = patterns
        self.user_name = None
        self.user_id = None
        self.running = True

        try:
            self.intent_classifier = get_intent_classifier()
            if self.intent_classifier:
                print("✅ Классификатор интентов загружен")
            else:
                print("⚠️ Классификатор интентов не загружен, использую старые паттерны")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки классификатора: {e}")
            self.intent_classifier = None

    def predict_intent(self, message):
        if self.intent_classifier:
            try:
                intent, confidence = self.intent_classifier.predict_with_confidence(message)
                print(f"🔍 Распознан интент: {intent} (уверенность: {confidence:.2f})")

                if confidence < 0.6:
                    return None
                return intent
            except Exception as e:
                print(f"Ошибка при предсказании интента: {e}")
                return None
        return None

    def extract_city(self, message):
        from patterns import extract_city_with_spacy
        return extract_city_with_spacy(message)

    def get_weather(self, city):
        from weather_api import get_weather
        return get_weather(city)

    def process_message(self, message):
        message = message.strip()

        if message.lower() == 'exit' or message.lower() == 'выход':
            self.running = False
            return "До свидания!"

        if self.user_name and not self.user_id:
            self.user_id = get_user_id_by_name(self.user_name)
        elif not self.user_id:
            self.user_id = -1

        current_state = get_last_user_state(self.user_id)
        if current_state:
            dialog_manager.set_state(self.user_id, current_state)

        state = dialog_manager.get_state(self.user_id)

        dialog_response = dialog_manager.process_message(self.user_id, message)

        new_state = dialog_manager.get_state(self.user_id)
        state_value = new_state.value

        if dialog_response is not None:
            log_message_to_db(message, dialog_response, self.user_id, state_value)
            return dialog_response

        if state == DialogState.START:
            intent = self.predict_intent(message)

            if intent:
                if intent == "weather" or intent == "weather_city_only":
                    city = self.extract_city(message)

                    if city:
                        response = self.get_weather(city)
                        log_message_to_db(message, response, self.user_id, state_value)
                        return response
                    else:
                        dialog_manager.set_state(self.user_id, DialogState.WAIT_CITY)
                        response = "В каком городе вас интересует погода?"
                        log_message_to_db(message, response, self.user_id, state_value)
                        return response

                # Обработка интента greeting
                elif intent == "greeting":
                    response = self.handle_greeting_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента farewell
                elif intent == "farewell":
                    response = self.handle_farewell_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента set_name
                elif intent == "set_name":
                    response = self.handle_set_name_intent(message)
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента help
                elif intent == "help":
                    response = self.handle_help_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента stats
                elif intent == "stats":
                    response = self.handle_stats_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента schedule
                elif intent == "schedule":
                    response = self.handle_schedule_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента yes_no
                elif intent == "yes_no":
                    response = self.handle_yes_no_intent()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

                # Обработка интента unknown
                elif intent == "unknown":
                    response = self.default_response()
                    log_message_to_db(message, response, self.user_id, state_value)
                    return response

        for pattern, handler in self.patterns:
            match = pattern.search(message)
            if match:
                if handler.__name__ == 'handle_name':
                    response = handler(match, self, self.user_id)
                else:
                    response = handler(match, self.user_id)

                log_message_to_db(message, response, self.user_id, state_value)
                return response

        response = self.default_response()
        log_message_to_db(message, response, self.user_id, state_value)
        return response

    def handle_greeting_intent(self):
        responses = [
            "Здравствуйте! Чем могу помочь?",
            "Привет! Как я могу вам помочь?",
            "Добрый день! Чем могу быть полезен?",
            "Приветствую! Задавайте вопросы."
        ]
        return random.choice(responses)

    def handle_farewell_intent(self):
        responses = [
            "До свидания! Хорошего дня!",
            "Пока! Было приятно пообщаться!",
            "Всего доброго! Возвращайтесь!",
            "До встречи! Хорошего настроения!"
        ]
        return random.choice(responses)

    def handle_set_name_intent(self, message):

        # Ищем имя в сообщении
        match = re.search(r"меня зовут\s+([а-яА-Яa-zA-Z]+)", message, re.IGNORECASE)
        if not match:
            match = re.search(r"я\s+([а-яА-Яa-zA-Z]+)", message, re.IGNORECASE)
        if not match:
            match = re.search(r"зовут\s+([а-яА-Яa-zA-Z]+)", message, re.IGNORECASE)

        if match:
            user_name = match.group(1)
            self.user_name = user_name
            user_id = save_user(user_name)
            self.user_id = user_id
            return f"Приятно познакомиться, {user_name}!"
        else:
            return "Как вас зовут? Скажите 'меня зовут [имя]'"

    def handle_help_intent(self):
        return """Я могу ответить на следующие запросы:
- Приветствие (привет, здравствуй, добрый день)
- Прощание (пока, до свидания)
- Погода (например: "Какая погода в Москве?" или просто "Какая погода?")
- Меня зовут [имя]
- Моя статистика
- Завтра идти на пары?
- Помощь

Также я поддерживаю диалог: если спросить "Какая погода?" без города,
я уточню город в следующем сообщении."""

    def handle_stats_intent(self):
        from database import get_user_stats
        if self.user_id and self.user_id > 0:
            stats = get_user_stats(self.user_id)
            if stats:
                return (f"📊 Ваша статистика:\n"
                        f"Имя: {stats['name']}\n"
                        f"Первый визит: {stats['first_seen']}\n"
                        f"Последний визит: {stats['last_seen']}\n"
                        f"Всего сообщений: {stats['messages_count']}\n"
                        f"Запросов погоды: {stats['weather_queries']}")
        return "Статистика недоступна. Сначала представьтесь (меня зовут [имя])"

    def handle_schedule_intent(self):
        from patterns import handle_YES_NO
        return handle_YES_NO()

    def handle_yes_no_intent(self):
        from patterns import handle_YES_NO
        return handle_YES_NO()

    def default_response(self):
        responses = [
            "Я не совсем понимаю. Может быть, переформулируете?",
            "Извините, я не умею отвечать на такие вопросы.",
            "Попробуйте спросить что-то другое или введите 'помощь'."
        ]
        return random.choice(responses)

    def run(self):
        print("=" * 50)
        print("Чат-бот запущен! Введите 'exit' или 'выход' для завершения.")
        print("Введите 'помощь' для списка команд.")
        if self.intent_classifier:
            print("🤖 Используется Word-Embeddings классификатор интентов")
        else:
            print("⚠️ Используются регулярные выражения (ML модель не загружена)")
        print("=" * 50)

        while self.running:
            try:
                user_input = input("\nВы: ")
                if not user_input.strip():
                    print("Бот: Пожалуйста, введите сообщение.")
                    continue

                response = self.process_message(user_input)
                print(f"Бот: {response}")

            except KeyboardInterrupt:
                print("\nБот: До свидания!")
                break
            except Exception as e:
                print(f"Бот: Произошла ошибка: {e}")
                if 'user_input' in locals():
                    log_message_to_db(user_input, f"Ошибка: {str(e)}", self.user_id)