from pydantic import BaseModel
from typing import Dict, List, Optional



class SheetData(BaseModel):
    text: str
    sheet_name: Optional[str] = None