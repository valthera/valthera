import json
from typing import Dict, Callable, List, Any, Optional
from valthera.models import UserContext, Behavior, ValtheraScores
from langchain_core.messages import SystemMessage, HumanMessage


class ReasoningEngine:
    """
    A configurable reasoning engine that applies BJ Fogg's Behavior Model (B=MAT).
    The decision logic is customizable via a set of rules.
    """

    def __init__(self, llm, decision_rules: Optional[List[Dict[str, Any]]] = None):
        """
        :param llm: A LangChain-compatible chat model (e.g., ChatOpenAI).
                    Must support the `_generate(...)` method returning an LLMResult.
        :param decision_rules: A list of rules defining how decisions are made.
        """
        self.llm = llm
        self.decision_rules = decision_rules if decision_rules is not None else self.default_decision_rules()

    def decide(
        self,
        user_context: UserContext,
        behavior: Behavior,
        scores: ValtheraScores,
        decision_rules: Optional[List[Dict[str, Any]]] = None
    ) -> Dict:
        """
        Returns a structured decision in JSON form based on configured rules.
        Allows passing custom decision rules at runtime.
        """
        rules = decision_rules if decision_rules is not None else self.decision_rules

        system_prompt = SystemMessage(
            content=(
                "You are an expert at applying BJ Fogg's Behavior Model (B=MAT). "
                "You must respond with valid JSON only—no code fences, no markdown. "
                "Do not include any extra keys beyond 'action' and 'analysis'."
            )
        )

        print(f">>>>> Scores: {scores.motivation:.2f}, {scores.ability:.2f}")

        user_prompt_text = (
            f"Behavior to evaluate:\n"
            f" - Name: {behavior.name}\n"
            f" - Description: {behavior.description}\n\n"
            f"Scores:\n"
            f" - Motivation: {scores.motivation:.2f}\n"
            f" - Ability: {scores.ability:.2f}\n\n"
            f"User context:\n{user_context}\n\n"
            "Decide on one of these actions:\n"
            " 1) trigger\n"
            " 2) improve_motivation\n"
            " 3) improve_ability\n"
            " 4) defer\n\n"
            "Use this logic:\n"
        )

        for rule in rules:
            user_prompt_text += f"- If ({rule['condition']}):\n    action = \"{rule['action']}\"  # {rule['description']}\n"

        user_prompt_text += (
            "\nIn the 'analysis' field, briefly explain the reasoning.\n\n"
            "Return ONLY valid JSON with exactly these two keys:\n"
            "{\n"
            "  \"action\": \"<trigger/improve_motivation/improve_ability/defer>\",\n"
            "  \"analysis\": \"<explanation>\"\n"
            "}\n\n"
            "IMPORTANT:\n"
            "- Do NOT include code fences/backticks.\n"
            "- No extra text or keys.\n"
            "- Stick to the logic above.\n"
        )

        user_message = HumanMessage(content=user_prompt_text)
        messages = [system_prompt, user_message]
        result = self.llm._generate(messages)
        response_message = result.generations[0].message
        response_text = response_message.content

        decision = self._parse_llm_response(response_text)
        return decision

    def _parse_llm_response(self, text: str) -> Dict:
        """
        Attempts to parse JSON from the LLM response. Falls back if not valid JSON.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "action": "defer",
                "analysis": f"Could not parse LLM response: {text}"
            }

    @staticmethod
    def default_decision_rules() -> List[Dict[str, Any]]:
        return [
            {"condition": "motivation >= 0.75 and ability >= 0.75", "action": "trigger", "description": "moderate ability is acceptable"},
            {"condition": "motivation < 0.75", "action": "improve_motivation", "description": "increase motivation"},
            {"condition": "ability < 0.75", "action": "improve_ability", "description": "increase ability"},
            {"condition": "otherwise", "action": "defer", "description": "not ready yet"},
        ]
