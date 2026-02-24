from typing import Any, Optional

from app.core.settings import get_settings

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency behavior
    genai = None


def get_gemini_model() -> Optional[Any]:
    settings = get_settings()
    if not settings.gemini_api_key or genai is None:
        return None

    try:
        genai.configure(api_key=settings.gemini_api_key)
        return genai.GenerativeModel(settings.gemini_model)
    except Exception:
        return None
