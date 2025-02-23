from pydantic import BaseModel, Extra
from typing import Dict, Any, Optional

class LangChainGraphConfig(BaseModel):
    entrypoint: Optional[str]
    nodes: Optional[Dict[str, Any]] = {}
    workflow: Optional[Dict[str, Any]] = {}
    entrypoint_set: Optional[bool] = False

    class Config:
        extra = Extra.allow
