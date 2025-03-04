# Valthera

## Overview
Valthera is a framework for creating behavior-driven notifications based on BJ Fogg's Behavior Model (B=MAT). It gathers data from different sources (like HubSpot, PostHog, and Snowflake), evaluates users' readiness for specific actions, and generates personalized triggers when appropriate.

By analyzing motivation and ability scores, Valthera helps determine the optimal time and messaging for user engagement.

## Core Concepts
Valthera is built around BJ Fogg's Behavior Model, which states that three elements must converge for a behavior to occur:

- **Motivation**: The user's desire to perform the behavior
- **Ability**: How easy it is for the user to perform the behavior
- **Trigger**: The prompt that initiates the behavior

The system calculates scores for motivation and ability based on user data, then determines whether a trigger should be sent and what message would be most effective.

## System Architecture
Valthera consists of five core components:

1. **DataAggregator**: Collects user data from multiple sources into a unified `UserContext`.
2. **ValtheraScorer**: Calculates motivation and ability scores based on configured metrics.
3. **ReasoningEngine**: Decides whether to trigger an action based on the scores.
4. **TriggerGenerator**: Creates personalized trigger messages when appropriate.
5. **ValtheraAgent**: Orchestrates the entire pipeline.

## Customization

### Custom Data Sources
Create your own data connector by implementing the `BaseConnector` interface:
```python
from valthera.connectors.base import BaseConnector

class MyCustomConnector(BaseConnector):
    def get_user_data(self, user_id: str):
        return {
            "custom_metric": 42,
            "last_activity": "2025-01-01"
        }
```
Then, register it in `DataAggregator`:
```python
data_aggregator = DataAggregator(connectors={"custom": MyCustomConnector()})
```

### Custom Scoring Configuration
Define scoring metrics to fit your needs:
```python
motivation_config = [
    {"key": "custom_metric", "weight": 0.5, "transform": lambda x: x / 100.0},
]
ability_config = [
    {"key": "last_activity", "weight": 0.5, "transform": lambda x: 1.0 if x == "recent" else 0.5},
]
scorer = ValtheraScorer(motivation_config, ability_config)
```

### Custom Decision Rules
Modify decision rules to determine when to send triggers:
```python
decision_rules = [
    {"condition": "motivation >= 0.7 and ability >= 0.7", "action": "trigger"},
    {"condition": "motivation < 0.7", "action": "improve_motivation"},
    {"condition": "ability < 0.7", "action": "improve_ability"},
]
reasoning_engine = ReasoningEngine(llm=custom_llm, decision_rules=decision_rules)
```

### Custom Trigger Messages
Control how the trigger message is generated:
```python
def custom_prompt(user_context):
    return f"Hey {user_context['email']}, check out this new feature!"

generator = TriggerGenerator(llm=custom_llm)
generator.generate_trigger(user_context, behavior, scores, custom_prompt)
```

## Examples
- **E-commerce Onboarding**: Increase conversions by nudging users at the right time.
- **SaaS Feature Adoption**: Help users discover and adopt new features effectively.
- **Healthcare Reminders**: Encourage patients to complete follow-ups and treatments.

## API Reference
See the full API documentation for detailed information on all classes and methods.

## Contributing
Contributions are welcome! Please submit a Pull Request or open an issue for discussion.