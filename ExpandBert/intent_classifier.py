# intent_classifier.py
import joblib
import os
import numpy as np

try:
    import spacy
    nlp = spacy.load("ru_core_news_md")
    USE_SPACY = True
except OSError:
    print("⚠️ Ошибка: Модель ru_core_news_md не найдена. Установите: python -m spacy download ru_core_news_md")
    USE_SPACY = False
    nlp = None


class IntentClassifier:
    def __init__(self, model_path="random_forest_model/"):
        self.model_path = model_path

        classifier_path = os.path.join(model_path, "classifier.pkl")

        if not os.path.exists(classifier_path):
            raise FileNotFoundError(f"Модель не найдена: {classifier_path}. Запустите train_model.py!")

        self.classifier = joblib.load(classifier_path)
        print(f"✅ Классификатор (Embeddings + LogReg) загружен, доступно {len(self.classifier.classes_)} интентов")

    def vectorize(self, text):
        if USE_SPACY and nlp:
            doc = nlp(text.lower().strip())
            return doc.vector
        else:
            return np.zeros(300)

    def predict(self, text):
        vector = self.vectorize(text).reshape(1, -1)
        return self.classifier.predict(vector)[0]

    def predict_with_confidence(self, text):
        vector = self.vectorize(text).reshape(1, -1)

        intent = self.classifier.predict(vector)[0]

        probabilities = self.classifier.predict_proba(vector)[0]
        confidence = max(probabilities)

        return intent, confidence

    def get_top_intents(self, text, top_k=3):
        vector = self.vectorize(text).reshape(1, -1)
        probabilities = self.classifier.predict_proba(vector)[0]

        top_indices = probabilities.argsort()[::-1][:top_k]

        top_intents = []
        for idx in top_indices:
            top_intents.append({
                'intent': self.classifier.classes_[idx],
                'confidence': probabilities[idx]
            })

        return top_intents


_intent_classifier = None


def get_intent_classifier():
    global _intent_classifier
    if _intent_classifier is None:
        try:
            _intent_classifier = IntentClassifier()
        except Exception as e:
            print(f"⚠️ Ошибка загрузки модели интентов: {e}")
            _intent_classifier = None
    return _intent_classifier