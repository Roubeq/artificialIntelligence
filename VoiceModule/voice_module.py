import os
import re
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

print("Загрузка модели Whisper...")
whisper_model = whisper.load_model("base")


def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\sа-яА-Я]", "", text)
    return text.strip()


def record_audio(filename="input.wav", seconds=4, fs=16000):
    print(f"🎤 Слушаю ({seconds} сек)...")
    try:
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        write(filename, fs, audio)
        return True
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return False


def speech_to_text(filename="input.wav"):
    if not os.path.exists(filename):
        return ""

    result = whisper_model.transcribe(filename, language="ru", fp16=False)
    raw_text = result.get("text", "")
    return clean_text(raw_text)


def listen_and_process():
    if record_audio():
        text = speech_to_text()
        if text:
            print(f"👂 Вы сказали: {text}")
        return text
    return ""