# intent_classifier_bert.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os


class BertIntentClassifier:
    def __init__(self, model_path="intent_model"):
        self.model_path = model_path

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель не найдена: {model_path}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

        self.id2label = {
            0: 'farewell',
            1: 'greeting',
            2: 'help',
            3: 'schedule',
            4: 'set_name',
            5: 'stats',
            6: 'unknown',
            7: 'weather',
            8: 'weather_city_only',
            9: 'yes_no'
        }

        self.label2id = {v: k for k, v in self.id2label.items()}

        print(f"✅ RuBERT классификатор загружен")
        print(f"📋 Доступные интенты: {list(self.id2label.values())}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def predict(self, text: str) -> str:
        text = text.lower().strip()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=32,
            padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        predicted_class = torch.argmax(outputs.logits, dim=1).item()

        return self.id2label.get(predicted_class, 'unknown')

    def predict_with_confidence(self, text: str):
        text = text.lower().strip()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=32,
            padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)

        intent = self.id2label.get(predicted_class.item(), 'unknown')
        confidence_score = confidence.item()

        return intent, confidence_score


_intent_classifier = None


def get_intent_classifier():
    global _intent_classifier
    if _intent_classifier is None:
        try:
            _intent_classifier = BertIntentClassifier()
        except Exception as e:
            print(f"⚠️ Ошибка загрузки RuBERT модели: {e}")
            _intent_classifier = None
    return _intent_classifier