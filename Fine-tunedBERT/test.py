#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import spacy

def test_city_extraction():
    try:
        nlp = spacy.load("ru_core_news_sm")
        print("✅ Модель spaCy успешно загружена")
    except OSError:
        print("❌ Ошибка: Модель ru_core_news_sm не найдена")
        print("Установите: python -m spacy download ru_core_news_sm")
        return

    test_phrases = [
        "Какая погода сегодня в Москве?",
        "Что с погодой в Санкт-Петербурге",

    ]

    for phrase in test_phrases:
        doc = nlp(phrase)

        print(f"\nФраза: '{phrase}'")

        entities = [(ent.text, ent.label_) for ent in doc.ents]
        if entities:
            print(f"  Распознанные сущности: {entities}")
        else:
            print("  Сущности не распознаны")

        cities = []
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:
                cities.append(ent.lemma_)

        if cities:
            print(f"  ✅ Найден город: {cities[0]}")
        else:
            print("  ❌ Город не найден")

        tokens_info = [(token.text, token.pos_, token.ent_type_) for token in doc]
        print(f"  Токены: {tokens_info}")


def main():
    test_city_extraction()

if __name__ == "__main__":
    main()