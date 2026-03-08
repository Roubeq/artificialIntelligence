#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bot_core import ChatBot

def main():
    try:
        bot = ChatBot()
        bot.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)