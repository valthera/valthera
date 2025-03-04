from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class Behavior:
    """
    Represents a target behavior we want the user to perform.
    """
    behavior_id: str
    name: str
    description: str
    # e.g., 'Complete Onboarding', 'Upgrade Subscription', 'Refer a Friend', etc.


@dataclass
class User:
    """
    Basic user data; might be partially from HubSpot or your identity system.
    """
    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # Add more fields if relevant (e.g., phone number, plan type, etc.)


@dataclass
class UserContext:
    """
    Aggregated data from HubSpot, Posthog, Snowflake, etc.,
    for a given user, relevant to B=MAT scoring.
    """
    user_id: str
    connector_data: Dict[str, Dict] = field(default_factory=dict)

    # Example derived fields
    # Could also be done in a 'feature engineering' step
    engagement_score: float = 0.0
    funnel_stage: Optional[str] = None
    usage_frequency: float = 0.0
    # ...other features for motivation/ability


@dataclass
class ValtheraScores:
    """
    Holds the B=MAT relevant scores or indicators.
    """
    motivation: float
    ability: float
    # Optionally store intermediate signals or reason
    notes: Optional[str] = None


@dataclass
class TriggerRecommendation:
    """
    Final recommendation for how to trigger the desired behavior.
    """
    trigger_message: str
    rationale: Optional[str] = None
    # Could also store recommended communication channel or timing
    channel: Optional[str] = None  # e.g. 'email', 'sms', 'in-app'
    confidence: Optional[float] = None  # <-- Add this
