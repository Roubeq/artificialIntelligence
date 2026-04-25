from enum import Enum
from typing import Any, Dict, Optional

from patterns import handle_weather_simple
import spacy

try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    print("Модель ru_core_news_sm не найдена. Установите: python -m spacy download ru_core_news_sm")
    nlp = None


class DialogState(Enum):
    START = "start"
    WAIT_CITY = "wait_city"


class DialogManager:
    def __init__(self):
        self.user_states: Dict[int, DialogState] = {}
        self.user_data: Dict[int, dict] = {}

    def get_skill_context(self, user_id: int) -> Dict[str, Any]:
        """Контекст для follow-up и скиллов: последний интент, реплики, слоты."""
        defaults = {
            "last_intent": None,
            "last_classifier_label": None,
            "last_user_text": None,
            "last_bot_reply": None,
            "last_city": None,
            "slots": {},
        }
        ctx = self.user_data.setdefault(user_id, {})
       # print(f"DEBUG: Current Intent: {intent}")
        #print(f"DEBUG: Last Intent in Context: {ctx.get('last_intent')}")
       # print(f"DEBUG: Saved City: {ctx.get('last_city')}")
        for key, default in defaults.items():
            if key not in ctx:
                ctx[key] = default.copy() if isinstance(default, dict) else default
        return ctx

    def record_conversation_turn(
        self,
        user_id: int,
        *,
        classifier_label: str,
        effective_intent: str,
        user_text: str,
        bot_reply: str,
    ) -> None:
        """Сохраняет хвост диалога: с ним можно строить follow-up и ответы скиллов."""
        ctx = self.get_skill_context(user_id)
        ctx["last_classifier_label"] = classifier_label
        if effective_intent != "unknown":
            ctx["last_intent"] = effective_intent
        ctx["last_user_text"] = user_text.strip()
        ctx["last_bot_reply"] = bot_reply

    def follow_up_snapshot(self, user_id: int) -> Dict[str, Any]:
        """Срез последнего полноценного ML-хода — удобно передавать в скиллы."""
        c = self.get_skill_context(user_id)
        return {
            "intent": c.get("last_intent"),
            "classifier_label": c.get("last_classifier_label"),
            "user_text": c.get("last_user_text"),
            "bot_reply": c.get("last_bot_reply"),
            "last_city": c.get("last_city"),
            "slots": dict(c.get("slots") or {}),
        }

    def get_state(self, user_id: int) -> DialogState:
        return self.user_states.get(user_id, DialogState.START)

    def set_state(self, user_id: int, state: DialogState) -> None:
        self.user_states[user_id] = state
        #print(f"Состояние пользователя {user_id}: {state.value}")

    def clear_user_data(self, user_id: int) -> None:
        if user_id in self.user_data:
            del self.user_data[user_id]

    def is_weather_request(self, text: str) -> bool:
        text_lower = text.lower()

        if nlp:
            doc = nlp(text_lower)
            for token in doc:
                if token.lemma_ in ['погода', 'температура', 'градус', 'холодно', 'тепло', 'прогноз']:
                    return True
                if token.lemma_ == 'сказать' and any(t.lemma_ == 'погода' for t in doc):
                    return True
        else:
            weather_keywords = ['погода', 'температура', 'градус', 'холодно', 'тепло', 'прогноз']
            if any(keyword in text_lower for keyword in weather_keywords):
                return True

        return False

    def process_message(self, user_id: int, text: str) -> Optional[str]:
        state = self.get_state(user_id)
        text_lower = text.lower().strip()

        if text_lower in ['exit', 'выход', 'отмена', 'cancel']:
            if state != DialogState.START:
                self.set_state(user_id, DialogState.START)
                self.clear_user_data(user_id)
                return "Диалог завершен. Чем еще могу помочь?"
            return None

        if state == DialogState.START:
            return self._handle_start_state(user_id, text)
        elif state == DialogState.WAIT_CITY:
            return self._handle_wait_city_state(user_id, text)

        return None

    def _handle_start_state(self, user_id: int, text: str) -> Optional[str]:
        if self.is_weather_request(text):
            weather_response = handle_weather_simple(text, user_id)

            if "Пожалуйста, укажите город" in weather_response:
                self.set_state(user_id, DialogState.WAIT_CITY)
                return "В каком городе вас интересует погода?"
            else:
                return weather_response

        return None

    def _handle_wait_city_state(self, user_id: int, text: str) -> str:
        city = text.strip()

        if not city or len(city) < 2:
            return "Пожалуйста, укажите корректное название города."

        self.get_skill_context(user_id)["last_city"] = city
        self.set_state(user_id, DialogState.START)

        weather_query = f"погода в {city}"
        print(f"Преобразованный запрос: '{weather_query}'")

        return handle_weather_simple(weather_query, user_id)


dialog_manager = DialogManager()