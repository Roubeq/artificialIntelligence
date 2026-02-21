from datetime import datetime


def log_message(user_message, bot_response):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("chat_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] USER: {user_message}\n")
        log_file.write(f"[{timestamp}] BOT: {bot_response}\n")
        log_file.write("-" * 50 + "\n")