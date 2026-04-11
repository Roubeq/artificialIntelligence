from dialog_manager import dialog_manager
from skills.datetime.datetime_skills import date_skill, time_skill
from skills.fallback import fallback
from skills.greeting.greeting_skill import greeting_skill
from skills.smalltalk.smalltalk_skill import smalltalk_skill
from skills.weather.weather_skill import weather_skill


def resolve_effective_intent(raw_intent: str, user_id: int) -> str:
    """Follow-up: подставляем последний сохранённый интент из контекста диалога."""
    ctx = dialog_manager.get_skill_context(user_id)
    if raw_intent == "follow_up":
        anchor = ctx.get("last_intent")
        return anchor if anchor else "unknown"
    return raw_intent


def route_intent(intent, text, user_id, bot=None):
    if intent in ("weather", "weather_city_only"):
        return weather_skill(text, user_id, intent)

    if intent == "time":
        return time_skill()

    if intent == "date":
        return date_skill()

    if intent == "greeting":
        return greeting_skill()

    if intent == "smalltalk":
        return smalltalk_skill()

    if bot is not None:
        if intent == "farewell":
            return bot.handle_farewell_intent()
        if intent == "help":
            return bot.handle_help_intent()
        if intent == "set_name":
            return bot.handle_set_name_intent(text)
        if intent == "stats":
            return bot.handle_stats_intent()
        if intent == "schedule":
            return bot.handle_schedule_intent()
        if intent == "yes_no":
            return bot.handle_yes_no_intent()
        if intent == "unknown":
            return bot.handle_unknown_intent()

    return fallback()
