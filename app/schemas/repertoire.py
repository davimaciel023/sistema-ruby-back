import datetime as dt
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SongCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    original_artist: str = ""
    key: str = Field(min_length=1, max_length=10)
    duration_seconds: int = Field(gt=0)
    bpm: int | None = None
    lyrics: str = ""
    chords: str = ""
    notes: str = ""


class SongUpdate(BaseModel):
    title: str | None = None
    original_artist: str | None = None
    key: str | None = None
    duration_seconds: int | None = None
    bpm: int | None = None
    lyrics: str | None = None
    chords: str | None = None
    notes: str | None = None


class SongOut(ORMModel):
    id: int
    title: str
    original_artist: str
    key: str
    duration_seconds: int
    bpm: int | None
    lyrics: str
    chords: str
    notes: str
    created_at: datetime


class RepertoireItemIn(BaseModel):
    song_id: int
    performed_key: str | None = None


class RepertoireCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_id: int | None = None
    date: dt.date | None = None
    gap_seconds: int = Field(default=30, ge=0)
    notes: str = ""
    items: list[RepertoireItemIn] = []


class RepertoireUpdate(BaseModel):
    name: str | None = None
    event_id: int | None = None
    date: dt.date | None = None
    gap_seconds: int | None = None
    notes: str | None = None
    items: list[RepertoireItemIn] | None = None


class RepertoireItemOut(ORMModel):
    id: int
    position: int
    performed_key: str | None
    song: SongOut


class RepertoireOut(ORMModel):
    id: int
    name: str
    event_id: int | None
    date: date | None
    gap_seconds: int
    notes: str
    created_at: datetime
    items: list[RepertoireItemOut] = []
    total_seconds: int = 0
