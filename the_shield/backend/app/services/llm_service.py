from typing import Optional

import httpx

from app.core.settings import get_settings
from app.services.local_model_loader import get_local_model_loader


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_loader = get_local_model_loader()

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

        if mode == "local":
            local_summary = self._summarize_with_local_model(prompt)
            if local_summary:
                return local_summary

        if mode == "ollama":
            ollama_summary = self._summarize_with_ollama(prompt)
            if ollama_summary:
                return ollama_summary

        return self._fallback_summary(
            parsed=parsed,
            status=status,
            missing_fields=missing_fields,
            domain_gaps=domain_gaps,
        )

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

    def _summarize_with_local_model(self, prompt: str) -> Optional[str]:
        try:
            self.local_loader.initialize()
            return self.local_loader.generate(
                instruction="Provide a concise requirement summary including risks and interpretation.",
                input_text=prompt,
                max_new_tokens=256
            )
        except Exception:
            return None

    def extract_capability_insights(self, text: str) -> Optional[dict]:
        """
        Calls the local LLM to extract structured capability insights.
        """
        mode = self.settings.llm_mode.strip().lower()
        if mode != "local":
            return None

        try:
            self.local_loader.initialize()
            instruction = (
                "Analyze the requirement and provide insights in JSON format.\n"
                "In 'proprietary_tool_suggestions', list 3-5 objects with 'name' and 'category' (strictly proprietary/commercial, NO open-source).\n"
                "In 'sprint_plan', provide a list of 3 sprint objects. Each sprint must have: "
                "'number' (int), 'goal' (string), 'timeline' (e.g. '2 Weeks'), and 'tasks' (list of objects).\n"
                "Each task must have 'task' (string), 'story_points' (1-8), and 'status'='todo'.\n"
                "Also include 'complexity_score' (0-100), 'decision_readiness_score' (0-100), 'top_concepts', 'investigation_actions', 'service_improvements', 'business_opportunities', 'stakeholder_communications', and 'visualization_recommendations'."
            )
            print(f"DEBUG: Generating LLM response for text length {len(text)}...")
            response = self.local_loader.generate(
                instruction=instruction,
                input_text=text,
                max_new_tokens=1024
            )
            print(f"DEBUG: Raw LLM Response: {response[:200]}...")
            if not response:
                return None
            
            import json
            import re
            
            # Extract JSON from markdown code blocks or raw text
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if not json_match:
                # Fallback to searching for the first { and last }
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    
                    # Coerce for Pydantic stability
                    if 'sprint_plan' not in data or not isinstance(data['sprint_plan'], list):
                        data['sprint_plan'] = []
                    else:
                        # Ensure each sprint has required fields
                        for s in data['sprint_plan']:
                            if not isinstance(s, dict): continue
                            if 'number' not in s: s['number'] = 1
                            if 'goal' not in s: s['goal'] = "Sprint Goal"
                            if 'timeline' not in s: s['timeline'] = "2 Weeks"
                            if 'tasks' not in s: s['tasks'] = []
                    
                    if 'proprietary_tool_suggestions' not in data or not isinstance(data['proprietary_tool_suggestions'], list):
                        data['proprietary_tool_suggestions'] = []
                    else:
                        # Coerce strings to objects if needed
                        normalized_tools = []
                        for t in data['proprietary_tool_suggestions']:
                            if isinstance(t, str):
                                normalized_tools.append({"name": t, "category": "Platform"})
                            elif isinstance(t, dict):
                                if 'name' not in t: t['name'] = "Unknown Tool"
                                if 'category' not in t: t['category'] = "Professional Tool"
                                normalized_tools.append(t)
                        data['proprietary_tool_suggestions'] = normalized_tools

                    return data
                except json.JSONDecodeError:
                    return None
            return None
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
