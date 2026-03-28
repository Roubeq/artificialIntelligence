import spacy
import numpy as np
import csv
import os
import joblib
from sklearn.linear_model import LogisticRegression

print("⏳ Загрузка языковой модели ru_core_news_md...")
try:
    nlp = spacy.load("ru_core_news_md")
except OSError:
    print("❌ Ошибка: Модель не найдена. Выполните: python -m spacy download ru_core_news_md")
    exit(1)

def vectorize(text):
    doc = nlp(text.lower().strip())
    return doc.vector

texts = []
labels = []
dataset_path = 'dataset.csv'

print(f"📂 Чтение датасета {dataset_path}...")
if not os.path.exists(dataset_path):
    print(f"❌ Файл {dataset_path} не найден!")
    exit(1)

with open(dataset_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if row.get('text') and row.get('intent'):
            texts.append(row['text'])
            labels.append(row['intent'])

print(f"✅ Загружено {len(texts)} примеров. Уникальных интентов: {len(set(labels))}")

print("🧠 Генерация векторов (это может занять время)...")
X = np.array([vectorize(t) for t in texts])
y = np.array(labels)

print("⚙️ Обучение логистической регрессии...")
model = LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0)
model.fit(X, y)

model_folder = "random_forest_model"
if not os.path.exists(model_folder):
    os.makedirs(model_folder)

joblib.dump(model, os.path.join(model_folder, "classifier.pkl"))

print(f"🎉 Готово! Модель сохранена в {model_folder}/classifier.pkl")

test_phrase = "осадки"
test_vec = vectorize(test_phrase).reshape(1, -1)
prediction = model.predict(test_vec)[0]
proba = max(model.predict_proba(test_vec)[0])
print(f"\n🧪 Тестовая проверка:")
print(f"Фраза: '{test_phrase}' -> Интент: {prediction} (Уверенность: {proba:.2f})")