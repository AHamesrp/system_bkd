from pydantic import BaseModel

class ItemUrl(BaseModel):
    key: str
    url: str

class Ok(BaseModel):
    ok: bool = True
