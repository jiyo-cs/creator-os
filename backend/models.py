from datetime import datetime
from typing import List

from pydantic import BaseModel


class Message(BaseModel):
    sender: str
    text: str
    timestamp: datetime


class Conversation(BaseModel):
    subscriber_id: str
    messages: List[Message]


class AnalyzeRequest(BaseModel):
    conversations: List[Conversation]
