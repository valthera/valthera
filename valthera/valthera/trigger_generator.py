from typing import Optional
import json
from valthera.models import (
    UserContext, Behavior, ValtheraScores, TriggerRecommendation
)
from langchain_core.messages import HumanMessage, SystemMessage


class TriggerGenerator:
    """
    Generates a short call-to-action or "trigger" message
    based on:
      - The target Behavior
      - The user's Motivation and Ability
      - (Optional) extra user context for personalization
      - Custom user-defined instructions for prompt customization
      - And provides a confidence score regarding how well this CTA
        is likely to encourage the desired behavior.
    """

    PROMPT_TEMPLATE = """
    We have:
      - Behavior: "{behavior_name}" (description: "{behavior_description}")
      - Motivation score: {motivation:.2f}
      - Ability score: {ability:.2f}
      - Relevant user context: {user_context}

    {custom_instructions}

    The user is presumably ready to perform this behavior because their
    Motivation × Ability is above a threshold.

    Please return a JSON object with two fields:
      1) "cta": a concise, persuasive call-to-action inviting the user to
      perform "{behavior_name}"
      2) "confidence": a numeric score between 0 and 1 reflecting
         how likely this CTA is to successfully prompt the user to do the behavior.

    Example output format:
    {{
      "cta": "Short CTA message here...",
      "confidence": 0.85
    }}
    """

    def __init__(self, llm):
        """
        :param llm: A LangChain-compatible chat model.
        """
        self.llm = llm

    def generate_trigger(
        self,
        user_context: UserContext,
        behavior: Behavior,
        scores: ValtheraScores,
        custom_instructions: Optional[str] = ""
    ) -> TriggerRecommendation:
        """
        Craft a message that addresses the user's readiness to perform 'behavior.name'
        given their motivation and ability, referencing user_context if desired.
        Allows for user-defined instructions to further customize the notification message.
        """
        system_message = SystemMessage(
            content="You are an AI assistant using BJ Fogg's Behavior Model (B=MAT)."
        )

        user_prompt_text = self.PROMPT_TEMPLATE.format(
            behavior_name=behavior.name,
            behavior_description=behavior.description,
            motivation=scores.motivation,
            ability=scores.ability,
            user_context=user_context,
            custom_instructions=custom_instructions or ""
        )

        user_message = HumanMessage(content=user_prompt_text)

        # Create a list of messages
        messages = [system_message, user_message]

        # Call _generate directly instead of generate
        result = self.llm._generate(messages)

        # Extract the response text
        response_text = result.generations[0].message.content

        # Parse the JSON from the LLM's response:
        cta_message = "Unable to parse CTA"
        confidence_score = None

        try:
            parsed_response = json.loads(response_text)
            cta_message = parsed_response.get("cta", cta_message)
            confidence_score = parsed_response.get("confidence", None)
        except json.JSONDecodeError:
            pass  # If the LLM didn't return valid JSON, fall back

        # Construct the TriggerRecommendation dataclass as the final output:
        return TriggerRecommendation(
            trigger_message=cta_message,
            rationale="Generated using BJ Fogg's model with user's M/A scores.",
            channel="email",  # or in-app, SMS, etc.
            confidence=confidence_score
        )
