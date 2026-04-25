import os
import re
import random
from patterns import patterns
from database import init_db, log_message_to_db, save_user, get_user_id_by_name, get_last_user_state
from dialog_manager import dialog_manager, DialogState
from intent_classifier_bert import get_intent_classifier
from skills.router import resolve_effective_intent, route_intent
from voice_module import listen_and_process

def _env_flag(name: str, default: bool = True) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


class ChatBot:
    def __init__(self, enable_tts: bool | None = None):
        init_db()
        self.patterns = patterns
        self.user_name = None
        self.user_id = None
        self.running = True
        self._tts = None
        if enable_tts is None:
            enable_tts = _env_flag("COQUI_TTS", True)
        if enable_tts:
            from coqui_tts import init_tts_service

            self._tts = init_tts_service()
            if self._tts:
                print("✅ Coqui TTS загружен (кэш и асинхронное воспроизведение)")

        try:
            self.intent_classifier = get_intent_classifier()
            if self.intent_classifier:
                print("✅ RuBERT классификатор интентов загружен")
            else:
                print("⚠️ Классификатор интентов не загружен, использую старые паттерны")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки классификатора: {e}")
            self.intent_classifier = None

    def predict_intent(self, message):
        if self.intent_classifier:
            try:
                intent, confidence = self.intent_classifier.predict_with_confidence(message)
                print(f"🔍 RuBERT -> интент: {intent} (уверенность: {confidence:.3f})")

                if confidence < 0.5: ## тут можно порог конфиденса поменять
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
        patterns = [
            r"меня зовут\s+([а-яА-Яa-zA-Z-]+)",
            r"я\s+([а-яА-Яa-zA-Z-]+)",
            r"зовут\s+([а-яА-Яa-zA-Z-]+)",
            r"называйте меня\s+([а-яА-Яa-zA-Z-]+)",
            r"зовите меня\s+([а-яА-Яa-zA-Z-]+)",
            r"моё имя\s+([а-яА-Яa-zA-Z-]+)",
            r"мое имя\s+([а-яА-Яa-zA-Z-]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                user_name = match.group(1).capitalize()
                self.user_name = user_name
                user_id = save_user(user_name)
                self.user_id = user_id
                return f"Приятно познакомиться, {user_name}!"

        return "Как вас зовут? Скажите 'меня зовут [имя]' или 'я [имя]'"

    def handle_help_intent(self):
        return """Я могу ответить на следующие запросы:
• Приветствие (привет, здравствуйте, добрый день)
• Прощание (пока, до свидания, всего доброго)
• Погода (например: "Какая погода в Москве?" или "Погода сейчас")
• Представиться (меня зовут [имя], я [имя])
• Расписание (завтра идти на пары? есть ли занятия?)
• Статистика (моя статистика, мои данные)
• Вопросы да/нет (стоит ли?, будет ли? нужно ли?)
• Помощь (что ты умеешь?, помощь)

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
        return self.handle_yes_no_intent()  # Переиспользуем логику да/нет

    def handle_yes_no_intent(self):
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

    def handle_unknown_intent(self):
        responses = [
            "Извините, я не понимаю этот вопрос.",
            "Я ещё не умею отвечать на такие запросы.",
            "Попробуйте переформулировать или спросите что-то другое.",
            "К сожалению, я не знаю ответа на этот вопрос."
        ]
        return random.choice(responses)

    def process_message(self, message):
        message = message.strip()

        if message.lower() in ['exit', 'выход', 'стоп', 'stop']:
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
        state_value = state.value

        dialog_response = dialog_manager.process_message(self.user_id, message)
        if dialog_response is not None:
            log_message_to_db(message, dialog_response, self.user_id, state_value)
            return dialog_response

        intent = self.predict_intent(message)

        if intent:
            effective_intent = resolve_effective_intent(intent, self.user_id)
            response = route_intent(effective_intent, message, self.user_id, bot=self)
            dialog_manager.record_conversation_turn(
                self.user_id,
                classifier_label=intent,
                effective_intent=effective_intent,
                user_text=message,
                bot_reply=response,
            )

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

    def voice_reply(self, user_text: str) -> str:
        from coqui_tts import normalize_text

        response = self.process_message(user_text)
        if self._tts and response:
            clean = normalize_text(response)
            self._tts.speak_async(clean)
        return response

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
            print("🤖 Используется RuBERT классификатор интентов")
        else:
            print("⚠️ Используются регулярные выражения (ML модель не загружена)")
        if self._tts:
            print("🔊 Озвучивание ответов: Coqui TTS (COQUI_TTS=0 чтобы отключить)")
        print("=" * 50)

        while self.running:
            try:
                user_input = input("\nВы (введите текст или 'v' для голоса): ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'выход']:
                    self.running = False
                    break

                if user_input.lower() == 'v':
                    user_text = listen_and_process()
                    if not user_text:
                        print("Бот: Я не смог разобрать речь.")
                        continue
                else:
                    user_text = user_input
                response = self.voice_reply(user_text)
                print(f"Бот: {response}")

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"Бот: Произошла ошибка: {e}")