from typing import Optional

import httpx

from app.core.config import get_gemini_model
from app.core.settings import get_settings


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None

    def summarize(
        self,
        text: str,
        parsed: dict,
        status: str,
        missing_fields: list[str],
        domain_gaps: list[str],
        questions: list[str],
    ) -> str:
        prompt = self._build_prompt(
            text=text,
            parsed=parsed,
            status=status,
            missing_fields=missing_fields,
            domain_gaps=domain_gaps,
            questions=questions,
        )
        mode = self.settings.llm_mode.strip().lower()

        if mode in {"auto", "ollama", "local"}:
            local_summary = self._summarize_with_ollama(prompt)
            if local_summary:
                return local_summary

        if mode in {"auto", "gemini"}:
            gemini_summary = self._summarize_with_gemini(prompt)
            if gemini_summary:
                return gemini_summary

        return self._fallback_summary(
            parsed=parsed,
            status=status,
            missing_fields=missing_fields,
            domain_gaps=domain_gaps,
        )

    def _summarize_with_gemini(self, prompt: str) -> Optional[str]:
        if self.model is None:
            self.model = get_gemini_model()
        if self.model is None:
            return None
        try:
            response = self.model.generate_content(prompt)
            response_text: Optional[str] = getattr(response, "text", None)
            if response_text:
                return response_text.strip()
        except Exception:
            return None
        return None

    def _summarize_with_ollama(self, prompt: str) -> Optional[str]:
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.post(
                    f"{self.settings.ollama_url.rstrip('/')}/api/generate",
                    json=payload,
                )
            if response.status_code != 200:
                return None
            body = response.json()
            text = body.get("response", "").strip()
            return text or None
        except Exception:
            return None

    @staticmethod
    def _build_prompt(
        text: str,
        parsed: dict,
        status: str,
        missing_fields: list[str],
        domain_gaps: list[str],
        questions: list[str],
    ) -> str:
        return (
            "You are a requirement engineering assistant.\n"
            "Summarize the requirement in 4-6 concise lines.\n"
            "Include interpretation and high-priority risks.\n\n"
            f"Requirement text: {text}\n"
            f"Parsed fields: {parsed}\n"
            f"Status: {status}\n"
            f"Missing fields: {missing_fields}\n"
            f"Domain gaps: {domain_gaps}\n"
            f"Clarification questions: {questions}\n"
        )

    @staticmethod
    def _fallback_summary(
        parsed: dict,
        status: str,
        missing_fields: list[str],
        domain_gaps: list[str],
    ) -> str:
        actor = parsed.get("actor") or "Unspecified actor"
        action = parsed.get("action") or "unspecified action"
        obj = parsed.get("obj") or "unspecified target"
        conditions = parsed.get("conditions") or "no explicit conditions"

        if status == "complete":
            return (
                f"The requirement indicates that {actor} should {action} {obj} "
                f"with {conditions}. No critical completeness gaps were detected."
            )
        if status == "incomplete":
            return (
                f"The requirement is incomplete. Parsed intent: {actor} -> {action} -> {obj}. "
                f"Missing fields: {', '.join(missing_fields)}."
            )

        return (
            f"The requirement appears functionally scoped to {actor} performing {action} on {obj}, "
            f"but domain-level gaps were found: {', '.join(domain_gaps)}."
        )
