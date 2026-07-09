from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    original_artist: Mapped[str] = mapped_column(String(200), default="")
    key: Mapped[str] = mapped_column(String(10))  # tom base, ex.: G, Am
    duration_seconds: Mapped[int] = mapped_column(Integer)  # duração aproximada
    bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lyrics: Mapped[str] = mapped_column(Text, default="")
    chords: Mapped[str] = mapped_column(Text, default="")  # cifra
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Repertoire(Base):
    __tablename__ = "repertoires"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gap_seconds: Mapped[int] = mapped_column(Integer, default=30)  # pausa entre músicas
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "RepertoireSong",
        back_populates="repertoire",
        cascade="all, delete-orphan",
        order_by="RepertoireSong.position",
        lazy="selectin",
    )


class RepertoireSong(Base):
    __tablename__ = "repertoire_songs"
    __table_args__ = (UniqueConstraint("repertoire_id", "song_id", name="uq_repertoire_song"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repertoire_id: Mapped[int] = mapped_column(ForeignKey("repertoires.id", ondelete="CASCADE"))
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    performed_key: Mapped[str | None] = mapped_column(String(10), nullable=True)  # tom executado

    repertoire = relationship("Repertoire", back_populates="items")
    song = relationship("Song", lazy="joined")
