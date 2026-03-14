# bot_core.py
import re
import random
from patterns import patterns
from database import init_db, log_message_to_db, save_user, get_user_id_by_name, get_last_user_state
from dialog_manager import dialog_manager, DialogState


class ChatBot:
    def __init__(self):
        init_db()
        self.patterns = patterns
        self.user_name = None
        self.user_id = None
        self.running = True

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

        dialog_response = dialog_manager.process_message(self.user_id, message)

        new_state = dialog_manager.get_state(self.user_id)
        state_value = new_state.value

        if dialog_response is not None:
            log_message_to_db(message, dialog_response, self.user_id, state_value)
            return dialog_response

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