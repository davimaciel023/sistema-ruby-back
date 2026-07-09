from datetime import datetime

from pydantic import BaseModel, Field

from app.models.study import MaterialStatus, MaterialType
from app.schemas.common import MemberBrief, ORMModel


class MaterialCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    type: MaterialType = MaterialType.link
    url: str = ""
    notes: str = ""
    owner_id: int | None = None
    status: MaterialStatus = MaterialStatus.to_study


class MaterialUpdate(BaseModel):
    title: str | None = None
    type: MaterialType | None = None
    url: str | None = None
    notes: str | None = None
    owner_id: int | None = None
    status: MaterialStatus | None = None


class MaterialOut(ORMModel):
    id: int
    title: str
    type: MaterialType
    url: str
    notes: str
    status: MaterialStatus
    created_at: datetime
    owner: MemberBrief | None
