"""
SQLModel database models for WealthLens.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid


def make_id() -> str:
    return uuid.uuid4().hex


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=make_id, primary_key=True)
    clerk_user_id: str = Field(unique=True, index=True)
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    households: list["Household"] = Relationship(back_populates="user")
    conversations: list["Conversation"] = Relationship(back_populates="user")


class Household(SQLModel, table=True):
    __tablename__ = "households"

    id: str = Field(default_factory=make_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    institution: str = ""
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="households")
    accounts: list["Account"] = Relationship(back_populates="household")
    extractions: list["Extraction"] = Relationship(back_populates="household")


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(default_factory=make_id, primary_key=True)
    household_id: str = Field(foreign_key="households.id", index=True)
    name: str = ""
    account_type: str = ""  # RRSP, TFSA, RESP, etc.
    total_value: float = 0.0

    household: Optional[Household] = Relationship(back_populates="accounts")
    holdings: list["Holding"] = Relationship(back_populates="account")


class Holding(SQLModel, table=True):
    __tablename__ = "holdings"

    id: str = Field(default_factory=make_id, primary_key=True)
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
    confidence: float = 0.5

    account: Optional[Account] = Relationship(back_populates="holdings")


class Extraction(SQLModel, table=True):
    __tablename__ = "extractions"

    id: str = Field(default_factory=make_id, primary_key=True)
    household_id: str = Field(foreign_key="households.id", index=True)
    pdf_s3_key: Optional[str] = None
    institution: str = ""
    holdings_count: int = 0
    confidence: float = 0.0
    raw_result: Optional[str] = None  # JSON string of extraction result
    created_at: datetime = Field(default_factory=datetime.utcnow)

    household: Optional[Household] = Relationship(back_populates="extractions")


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=make_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="conversations")
    messages: list["ConversationMessage"] = Relationship(back_populates="conversation")


class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_messages"

    id: str = Field(default_factory=make_id, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str = "user"  # user, assistant, system
    content: str = ""
    widgets_snapshot: Optional[str] = None  # JSON of widgets at this point
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Optional[Conversation] = Relationship(back_populates="messages")
