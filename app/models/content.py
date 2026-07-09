import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Platform(str, enum.Enum):
    instagram = "instagram"
    tiktok = "tiktok"
    youtube = "youtube"
    other = "other"


class PostStatus(str, enum.Enum):
    idea = "idea"
    producing = "producing"
    scheduled = "scheduled"
    posted = "posted"


class Post(Base):
    """Item do cronograma de postagens."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), default=Platform.instagram)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    theme: Mapped[str] = mapped_column(String(255))
    responsible_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.idea)
    link: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    responsible = relationship("Member", lazy="joined")


class VideoIdeaStatus(str, enum.Enum):
    idea = "idea"
    producing = "producing"
    posted = "posted"


class VideoIdea(Base):
    __tablename__ = "video_ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    responsible_id: Mapped[int | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    status: Mapped[VideoIdeaStatus] = mapped_column(
        Enum(VideoIdeaStatus), default=VideoIdeaStatus.idea
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    responsible = relationship("Member", lazy="joined")
