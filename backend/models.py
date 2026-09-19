from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# =========================
# MESSAGES
# =========================

class Message(BaseModel):

    sender: str
    text: str
    timestamp: datetime


class Conversation(BaseModel):

    subscriber_id: str
    messages: List[Message]


class AnalyzeRequest(BaseModel):

    conversations: List[Conversation]


# =========================
# WORKSPACE
# =========================

class Workspace(BaseModel):

    id: str
    name: str

    created_at: Optional[
        datetime
    ] = None


# =========================
# CREATOR
# =========================

class Creator(BaseModel):

    id: str
    workspace_id: str

    name: str

    platform: str = "instagram"

    username: Optional[str] = None

    created_at: Optional[
        datetime
    ] = None


# =========================
# USER
# =========================

class User(BaseModel):

    id: str

    email: str

    name: Optional[str] = None

    created_at: Optional[
        datetime
    ] = None


# =========================
# MEMBERSHIP
# =========================

class Membership(BaseModel):

    user_id: str

    workspace_id: str

    role: str = "member"


# =========================
# IMPORT
# =========================

class ImportResult(BaseModel):

    filename: str

    status: str

    normalized_conversations: int

    skipped_rows: int

    total_stored_conversations: int


# =========================
# CREATOR CONTEXT
# =========================

class CreatorContext(BaseModel):

    workspace_id: str

    creator_id: str
