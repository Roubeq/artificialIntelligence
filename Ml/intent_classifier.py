import joblib
import re
import os

try:
    import spacy

    nlp = spacy.load("ru_core_news_sm")
    USE_SPACY = True
except:
    USE_SPACY = False
    nlp = None


class IntentClassifier:
    def __init__(self, model_path="random_forest_model/"):
        self.model_path = model_path

        vectorizer_path = os.path.join(model_path, "vectorizer.pkl")
        classifier_path = os.path.join(model_path, "classifier.pkl")

        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Векторизатор не найден: {vectorizer_path}")
        if not os.path.exists(classifier_path):
            raise FileNotFoundError(f"Модель не найдена: {classifier_path}")

        self.vectorizer = joblib.load(vectorizer_path)
        self.classifier = joblib.load(classifier_path)

        print(f"Модель загружена, доступно {len(self.classifier.classes_)} интентов")

    def preprocess(self, text):
        if USE_SPACY and nlp:
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

    def predict(self, text):
        processed = self.preprocess(text)
        vector = self.vectorizer.transform([processed])
        return self.classifier.predict(vector)[0]

    def predict_with_confidence(self, text):
        processed = self.preprocess(text)
        vector = self.vectorizer.transform([processed])

        intent = self.classifier.predict(vector)[0]

        probabilities = self.classifier.predict_proba(vector)[0]
        confidence = max(probabilities)

        return intent, confidence

    def get_top_intents(self, text, top_k=3):
        processed = self.preprocess(text)
        vector = self.vectorizer.transform([processed])

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
            print(f"⚠️ Ошибка загрузки модели: {e}")
            _intent_classifier = None
    return _intent_classifier