"""
SQLModel database models for WealthLens.

NOTE: Supabase SQL migration is the source of truth for schema.
These models are kept as reference / for type hints only.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid


class Profile(SQLModel, table=True):
    """Maps to Supabase auth.users via profiles table."""
    __tablename__ = "profiles"

    id: str = Field(primary_key=True)  # Supabase auth UUID
    email: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Household(SQLModel, table=True):
    __tablename__ = "households"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="profiles.id", index=True)
    institution: str = ""
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    household_id: str = Field(foreign_key="households.id", index=True)
    name: str = ""
    account_type: str = ""
    total_value: float = 0.0


class Holding(SQLModel, table=True):
    __tablename__ = "holdings"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    account_id: str = Field(foreign_key="accounts.id", index=True)
    symbol: str = ""
    name: str = ""
    quantity: float = 0.0
    market_value: float = 0.0
    book_cost: Optional[float] = None
    mer: Optional[float] = None
    sector: Optional[str] = None
    asset_class: Optional[str] = None
    currency: str = "CAD"
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    confidence: float = 0.5


class Extraction(SQLModel, table=True):
    __tablename__ = "extractions"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    household_id: str = Field(foreign_key="households.id", index=True)
    institution: str = ""
    holdings_count: int = 0
    confidence: float = 0.0
    raw_result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="profiles.id", index=True)
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_messages"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str = "user"
    content: str = ""
    widgets_snapshot: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
