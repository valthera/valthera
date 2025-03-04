# langchain-valthera

This package contains the LangChain integration with Valthera

## Installation

```bash
pip install -U langchain-valthera
```

And you should configure credentials by setting the following environment variables:

OPENAI_API_KEY=open-ai-api-key

## Valthera Tools

`ValtheraTool` class exposes the tool from Valthera.

```python
class CustomDataSource(BaseConnector):
    """    
    Implement your data source
    """
    def get_user_data(self, user_id: str):
        return {
            ...
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,  # 100 -> lead_score_factor = 1.0
            "company_name": "MaxMotivation Corp.",
            "last_contacted_date": "2023-09-20",
            "marketing_emails_opened": 20,
            "marketing_emails_clicked": 10,
            ...
        }


data_aggregator = DataAggregator(
    connectors={
        "custom": CustomDataSource(),        
    }
)

reasoning_engine = ReasoningEngine(
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

trigger_generator = TriggerGenerator(
    llm=MockChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)


motivation_config = [
    {"key": "lead_score", "weight": 0.30, "transform": lambda x: min(x, 100) / 100.0},
    {"key": "events_count_past_30days", "weight": 0.30, "transform": lambda x: min(x, 50) / 50.0},
    {"key": "marketing_emails_opened", "weight": 0.20, "transform": lambda x: min(x / 10.0, 1.0)},
    {"key": "session_count", "weight": 0.20, "transform": lambda x: min(x / 5.0, 1.0)}
]

ability_config = [
    {"key": "onboarding_steps_completed", "weight": 0.30, "transform": lambda x: min(x / 5.0, 1.0)},
    {"key": "session_count", "weight": 0.30, "transform": lambda x: min(x / 10.0, 1.0)},
    {"key": "behavior_complexity", "weight": 0.40, "transform": lambda x: 1 - (min(x, 5) / 5.0)}
]

scorer = ValtheraScorer(motivation_config, ability_config)

valthera_tool = ValtheraTool(
    motivation_config=motivation_config,
    ability_config=ability_config,
    reasoning_engine=reasoning_engine,
    trigger_generator=trigger_generator,
    data_aggregator=mock_data_aggregator
)
```