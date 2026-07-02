from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class MongoModel(BaseModel):
    """Base Pydantic model with Mongo alias support and timestamps."""

    id: str | None = Field(default=None, alias='_id')
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    def to_mongo(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True, exclude_none=True)
        if data.get('_id') is None:
            data.pop('_id', None)
        return data


class User(MongoModel):
    """Discord user profile stored per guild."""

    user_id: int
    guild_id: int
    display_name: str
    timezone: str = 'UTC'
    privacy_level: Literal['private', 'partner', 'shared'] = 'partner'


class Couple(MongoModel):
    """Relationship link between two Discord users."""

    guild_id: int
    partner_a_id: int
    partner_b_id: int
    linked_at: datetime = Field(default_factory=now_utc)
    anniversary: datetime | None = None
    status: Literal['pending', 'active', 'paused', 'ended'] = 'pending'


class Complaint(MongoModel):
    """Mediated concern raised by one partner."""

    couple_id: str
    author_id: int
    text: str
    status: Literal['open', 'mediated', 'resolved'] = 'open'
    mediation: str | None = None


class Mood(MongoModel):
    """Single mood tracking entry."""

    couple_id: str
    user_id: int
    score: int
    note: str | None = None


class Journal(MongoModel):
    """Private or shared journal entry."""

    couple_id: str
    user_id: int
    title: str
    body: str


class Memory(MongoModel):
    """Positive relationship memory with tags."""

    couple_id: str
    author_id: int
    text: str
    tags: list[str] = Field(default_factory=list)


class Quote(MongoModel):
    """Saved meaningful quote."""

    couple_id: str
    text: str
    author: str | None = None


class Goal(MongoModel):
    """Shared relationship goal with completion state."""

    couple_id: str
    title: str
    owner_id: int | None = None
    due_at: datetime | None = None
    completed: bool = False


class Reminder(MongoModel):
    """Scheduled relationship reminder."""

    couple_id: str
    user_id: int
    message: str
    remind_at: datetime
    delivered: bool = False


class Promise(MongoModel):
    """Promise made by a partner."""

    couple_id: str
    promiser_id: int
    text: str
    kept: bool = False


class Achievement(MongoModel):
    """Awarded relationship achievement."""

    couple_id: str
    key: str
    title: str
    awarded_at: datetime = Field(default_factory=now_utc)


class Visit(MongoModel):
    """Visit countdown or visit-related log."""

    couple_id: str
    user_id: int
    command: str


class Wishlist(MongoModel):
    """Gift or experience wishlist."""

    couple_id: str
    user_id: int
    items: list[str] = Field(default_factory=list)


class Gift(MongoModel):
    """Gift record between partners."""

    couple_id: str
    giver_id: int
    recipient_id: int
    description: str


class AIMemory(MongoModel):
    """Persistent AI context memory."""

    couple_id: str
    text: str
    importance: int = 1


class ConversationSummary(MongoModel):
    """Summarized conversation history for AI context."""

    couple_id: str
    summary: str
    message_count: int = 0


class Settings(MongoModel):
    """Guild or couple configuration document."""

    guild_id: int
    couple_id: str | None = None
    counselor_enabled: bool = True
    logging_channel_id: int | None = None
