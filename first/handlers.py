import re
from patterns import patterns
from logger import log_message
import random

class ChatBot:
    def __init__(self):
        self.patterns = patterns
        self.user_name = None
        self.running = True

    def process_message(self, message):
        message = message.strip()

        if message.lower() == 'exit' or message.lower() == 'выход':
            self.running = False
            return "До свидания!"

        for pattern, handler in self.patterns:
            match = pattern.search(message)
            if match:
                if handler.__name__ == 'handle_name':
                    return handler(match, self)
                return handler(match)

        return self.default_response()

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
        print("=" * 50)

        while self.running:
            try:
                user_input = input("\nВы: ")
                user_input.lower()
                if not user_input.strip():
                    print("Бот: Пожалуйста, введите сообщение.")
                    continue

                response = self.process_message(user_input)
                print(f"Бот: {response}")

                log_message(user_input, response)

            except KeyboardInterrupt:
                print("\nБот: До свидания!")
                break
            except Exception as e:
                print(f"Бот: Произошла ошибка: {e}")