import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaterialType(str, enum.Enum):
    link = "link"
    pdf = "pdf"
    video = "video"
    chord_chart = "chord_chart"  # cifra


class MaterialStatus(str, enum.Enum):
    to_study = "to_study"
    studying = "studying"
    mastered = "mastered"


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[MaterialType] = mapped_column(Enum(MaterialType), default=MaterialType.link)
    url: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("members.id"), nullable=True
    )  # nulo = material da banda toda
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus), default=MaterialStatus.to_study
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Member", lazy="joined")
