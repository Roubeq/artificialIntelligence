"""
Coqui TTS: предзагрузка модели, кэш WAV, асинхронное воспроизведение (threading).
YourTTS: задайте COQUI_TTS_SPEAKER_WAV (референсный wav) и COQUI_TTS_LANGUAGE (например ru).
Без референса для your_tts используется fallback: en/ljspeech/tacotron2-DDC.
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from anyascii import anyascii

_YOUR_TTS = "tts_models/multilingual/multi-dataset/your_tts"
_FALLBACK_SAFE = "tts_models/en/ljspeech/tacotron2-DDC"


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\bkm\b", "kilometers", text, flags=re.IGNORECASE)
    text = re.sub(r"\bкм\b", "километров", text, flags=re.IGNORECASE)
    text = re.sub(r"\bкм/ч\b", "километров в час", text, flags=re.IGNORECASE)
    text = re.sub(r"\b°C\b|°\s*[Cc]", "градусов цельсия", text)
    text = re.sub(r"\d+", lambda m: str(int(m.group())), text)
    text = re.sub(r"[\U0001F300-\U0001FAFF]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


class CoquiTTSService:
    def __init__(
        self,
        *,
        cache_dir: Optional[Path] = None,
        model_name: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        language: Optional[str] = None,
        progress_bar: bool = False,
    ) -> None:
        from TTS.api import TTS

        self._progress_bar = progress_bar
        self._cache_dir = Path(cache_dir or Path(__file__).resolve().parent / "cache" / "tts_wav")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        env_model = os.environ.get("COQUI_TTS_MODEL")
        env_speaker = os.environ.get("COQUI_TTS_SPEAKER_WAV")
        env_lang = os.environ.get("COQUI_TTS_LANGUAGE", "ru")

        self._model_name = model_name or env_model or _YOUR_TTS
        self._speaker_wav = speaker_wav or env_speaker
        self._language = language or env_lang

        use_your_tts = "your_tts" in self._model_name.lower()
        if use_your_tts and not self._speaker_wav:
            print(
                "ℹ️ COQUI_TTS_SPEAKER_WAV не задан — YourTTS без референса недоступен, "
                f"используется fallback: {_FALLBACK_SAFE}"
            )
            self._model_name = _FALLBACK_SAFE
            self._speaker_wav = None

        self._tts = TTS(model_name=self._model_name, progress_bar=self._progress_bar)
        self._memory_cache: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._warned_translit = False

    def preload(self, warmup_text: str = "System is ready.") -> None:
        path = self._cache_dir / "warmup.wav"
        self._synthesize(warmup_text, path)

    def _synthesize(self, text: str, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        text_for_tts = self._prepare_text_for_model(text)
        kwargs: Dict[str, Any] = {"text": text_for_tts, "file_path": str(out_path)}
        if self._speaker_wav:
            kwargs["speaker_wav"] = self._speaker_wav
            kwargs["language"] = self._language

        try:
            self._tts.tts_to_file(speed=0.9, **kwargs)
        except TypeError:
            try:
                self._tts.tts_to_file(**kwargs)
            except TypeError:
                self._tts.tts_to_file(text=text_for_tts, file_path=str(out_path))

    def _prepare_text_for_model(self, text: str) -> str:
        if not text:
            return text
        # Английская fallback-модель не знает кириллицу; транслитерируем.
        if self._model_name == _FALLBACK_SAFE and re.search(r"[А-Яа-яЁё]", text):
            if not self._warned_translit:
                print("ℹ️ Для fallback en/ljspeech включена транслитерация кириллицы.")
                self._warned_translit = True
            return anyascii(text)
        return text

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        path = self._cache_dir / f"{_cache_key(text)}.wav"
        self._synthesize(text, path)
        self._play(path)

    def speak_cached(self, text: str) -> None:
        if not text.strip():
            return
        with self._lock:
            path = self._memory_cache.get(text)
            if path is None:
                path = str(self._cache_dir / f"{_cache_key(text)}.wav")
                self._synthesize(text, Path(path))
                self._memory_cache[text] = path
        self._play(path)

    def _play(self, path: Path | str) -> None:
        path_str = str(path)
        try:
            import winsound

            winsound.PlaySound(path_str, winsound.SND_FILENAME)
            return
        except Exception:
            pass

        try:
            import playsound

            playsound.playsound(path_str, block=True)
            return
        except Exception as e:
            print(f"⚠️ Ошибка воспроизведения аудио: {e}")

    def speak_async(self, text: str) -> None:
        threading.Thread(target=self.speak_cached, args=(text,), daemon=True).start()


_tts_singleton: Optional[CoquiTTSService] = None


def get_tts_service() -> Optional[CoquiTTSService]:
    return _tts_singleton


def init_tts_service(**kwargs: Any) -> Optional[CoquiTTSService]:
    global _tts_singleton
    if _tts_singleton is not None:
        return _tts_singleton
    try:
        _tts_singleton = CoquiTTSService(**kwargs)
    except Exception as e:
        print(f"⚠️ Coqui TTS недоступен: {e}")
        _tts_singleton = None
        return None
    try:
        _tts_singleton.preload()
    except Exception as e:
        print(f"⚠️ TTS предзагрузка (warmup): {e}")
    return _tts_singleton
