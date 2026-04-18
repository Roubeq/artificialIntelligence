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

        self.id2label, self.label2id = self._load_label_maps()

        print(f"✅ RuBERT классификатор загружен")
        print(f"📋 Доступные интенты: {list(self.id2label.values())}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _load_label_maps(self):
        cfg = self.model.config
        n = int(cfg.num_labels)

        def from_labels_file():
            path = os.path.join(self.model_path, "labels.txt")
            if not os.path.isfile(path):
                return None
            with open(path, encoding="utf-8") as f:
                labels = [ln.strip() for ln in f if ln.strip()]
            if len(labels) != n:
                return None
            id2label = {i: lab for i, lab in enumerate(labels)}
            return id2label, {lab: i for i, lab in id2label.items()}

        def from_config():
            if not cfg.id2label:
                return None
            sample = next(iter(cfg.id2label.values()))
            if isinstance(sample, str) and sample.startswith("LABEL_"):
                return None
            id2label = {int(k): v for k, v in cfg.id2label.items()}
            if len(id2label) != n:
                return None
            return id2label, {v: k for k, v in id2label.items()}

        legacy = {
            0: "date",
            1: "farewell",
            2: "greeting",
            3: "help",
            4: "schedule",
            5: "set_name",
            6: "smalltalk",
            7: "stats",
            8: "time",
            9: "unknown",
            10: "weather",
            11: "weather_city_only",
            12: "yes_no",
        }

        for loader in (from_config, from_labels_file):
            maps = loader()
            if maps:
                return maps

        if n == len(legacy):
            return legacy, {v: k for k, v in legacy.items()}

        raise ValueError(
            f"Не удалось сопоставить классы модели (num_labels={n}). "
            "Переобучите модель: python train_intent_model.py"
        )

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