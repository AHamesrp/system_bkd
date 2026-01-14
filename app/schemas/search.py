from typing import List, Optional
from pydantic import BaseModel
from .common import ItemUrl

class SearchOut(BaseModel):
    count: int
    items: List[ItemUrl]
    zip: Optional[str] = None
