import csv
import re
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from collections import Counter
import os
import sys

USE_SPACY = False
try:
    import spacy
    try:
        nlp = spacy.load("ru_core_news_sm")
        USE_SPACY = True
    except OSError:
        USE_SPACY = False
except ImportError:
    USE_SPACY = False


def preprocess_text(text):
    if USE_SPACY:
        doc = nlp(text.lower().strip())
        tokens = []
        for token in doc:
            if not token.is_stop and not token.is_punct and not token.is_space:
                if len(token.lemma_) > 2 or token.lemma_.isdigit():
                    tokens.append(token.lemma_)
        return " ".join(tokens)
    else:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text


def load_dataset(csv_file="intent_dataset_final.csv"):
    texts = []
    labels = []

    print(f"\nЗагрузка датасета из {csv_file}...")

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        print("Сначала запустите create_final_dataset.py для создания датасета")
        sys.exit(1)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = preprocess_text(row['text'])
            texts.append(text)
            labels.append(row['intent'])

    print(f"Загружено {len(texts)} примеров")
    print(f"Уникальных интентов: {len(set(labels))}")

    intent_counts = Counter(labels)
    print("\nРаспределение по интентам:")
    for intent, count in sorted(intent_counts.items()):
        percentage = (count / len(texts)) * 100
        print(f"  {intent:20s}: {count:3d} примеров ({percentage:.1f}%)")

    if len(texts) > 0:
        print(f"\nПример предобработки:")
        original = next(row for row in open(csv_file, 'r', encoding='utf-8') if row.strip())
        if original:
            original_text = original.split(',')[0].strip('"')
            print(f"   Оригинал: {original_text}")
            print(f"   Обработан: {texts[0]}")

    return texts, labels


def train_random_forest(X_train, X_test, y_train, y_test):
    print("\n" + "=" * 60)
    print("Обучение Random Forest классификатора")
    print("=" * 60)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )

    print("Обучение модели...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nОбучение завершено!")
    print(f"Точность на тестовой выборке: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    return model, y_pred


def save_model(vectorizer, model, output_dir="random_forest_model"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    joblib.dump(vectorizer, f"{output_dir}/vectorizer.pkl")
    joblib.dump(model, f"{output_dir}/classifier.pkl")


    print(f"\nМодель сохранена в: {output_dir}/")
    print(f"   - vectorizer.pkl")
    print(f"   - classifier.pkl")

    return output_dir


def test_model(model, vectorizer, test_examples):
    print("\n" + "=" * 60)
    print("Тестирование модели на примерах")
    print("=" * 60)

    for text in test_examples:
        processed = preprocess_text(text)
        vector = vectorizer.transform([processed])

        intent = model.predict(vector)[0]
        probabilities = model.predict_proba(vector)[0]
        confidence = max(probabilities)

        print(f"\n📝 '{text}'")
        if USE_SPACY:
            print(f"   Обработано: '{processed}'")
        print(f"   Интент: {intent} (уверенность: {confidence:.4f})")


def main():
    print("=" * 60)
    print("RANDOM FOREST - Обучение классификатора интентов")
    print("=" * 60)

    texts, labels = load_dataset("intent_dataset_final.csv")

    print("\nСоздание TF-IDF векторизатора...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )

    # 3. Векторизация
    X = vectorizer.fit_transform(texts)
    y = np.array(labels)

    print(f"Векторизация завершена")
    print(f"Размер матрицы: {X.shape[0]} примеров, {X.shape[1]} признаков")

    print("\nРазделение данных...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    total_samples = X.shape[0]
    print(f"   Обучающая: {X_train.shape[0]} примеров ({X_train.shape[0] / total_samples * 100:.1f}%)")
    print(f"   Тестовая: {X_test.shape[0]} примеров ({X_test.shape[0] / total_samples * 100:.1f}%)")

    # 5. Обучение
    model, y_pred = train_random_forest(X_train, X_test, y_train, y_test)

    # 6. Сохранение
    save_model(vectorizer, model, "random_forest_model")

    print("Модель успешно обучена и сохранена!")


if __name__ == "__main__":
    main()