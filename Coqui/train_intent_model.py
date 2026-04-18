import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from datasets import Dataset
import warnings
warnings.filterwarnings('ignore')
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

df = pd.read_csv("dataset.csv")
df = df[~df['intent'].isin(['farewall', 'intent'])]
df = df.drop_duplicates(subset=['text'])
df = df.dropna()

intents = sorted(df['intent'].unique())
label2id = {label: i for i, label in enumerate(intents)}
id2label = {i: label for label, i in label2id.items()}
df['label'] = df['intent'].map(label2id)

print(f"   Интенты: {intents}")
print(f"   Всего: {len(df)} примеров")

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['text'].tolist(), df['label'].tolist(), test_size=0.2, random_state=42
)

tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")

train_enc = tokenizer(train_texts, padding=True, truncation=True, max_length=32, return_tensors="pt")
val_enc = tokenizer(val_texts, padding=True, truncation=True, max_length=32, return_tensors="pt")

train_dataset = Dataset.from_dict({
    'input_ids': train_enc['input_ids'],
    'attention_mask': train_enc['attention_mask'],
    'label': train_labels
})
val_dataset = Dataset.from_dict({
    'input_ids': val_enc['input_ids'],
    'attention_mask': val_enc['attention_mask'],
    'label': val_labels
})

model = AutoModelForSequenceClassification.from_pretrained(
    "DeepPavlov/rubert-base-cased",
    num_labels=len(intents),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True,
)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    eval_strategy="epoch",  # тут выдавало ошибку
    save_strategy="no",
    logging_steps=10,
    report_to="none",
    disable_tqdm=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

trainer.train()

out_dir = "intent_model"
model.save_pretrained(out_dir)
tokenizer.save_pretrained(out_dir)
with open(os.path.join(out_dir, "labels.txt"), "w", encoding="utf-8") as lf:
    lf.write("\n".join(intents))