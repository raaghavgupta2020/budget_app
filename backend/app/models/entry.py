from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import uuid4

class EntryBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: Literal["Income", "Expense"]
    date: datetime = Field(default_factory=datetime.utcnow)
    amount: float

class EntryCreate(EntryBase):
    pass

class EntryUpdate(EntryBase):
    pass

class Entry(EntryBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EntryInDB(Entry):
    pass

class EntryFilter(BaseModel):
    type: Optional[Literal["Income", "Expense"]] = None
    search: Optional[str] = None
    sort_by: Optional[Literal["amount", "date"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = None