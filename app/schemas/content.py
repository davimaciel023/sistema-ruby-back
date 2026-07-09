from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.content import Platform, PostStatus, VideoIdeaStatus
from app.schemas.common import MemberBrief, ORMModel


class PostCreate(BaseModel):
    platform: Platform = Platform.instagram
    planned_date: date
    theme: str = Field(min_length=1, max_length=255)
    responsible_id: int
    status: PostStatus = PostStatus.idea
    link: str = ""


class PostUpdate(BaseModel):
    platform: Platform | None = None
    planned_date: date | None = None
    theme: str | None = None
    responsible_id: int | None = None
    status: PostStatus | None = None
    link: str | None = None


class PostOut(ORMModel):
    id: int
    platform: Platform
    planned_date: date
    theme: str
    status: PostStatus
    link: str
    created_at: datetime
    responsible: MemberBrief


class VideoIdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    responsible_id: int | None = None
    status: VideoIdeaStatus = VideoIdeaStatus.idea


class VideoIdeaUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    responsible_id: int | None = None
    status: VideoIdeaStatus | None = None


class VideoIdeaOut(ORMModel):
    id: int
    title: str
    description: str
    status: VideoIdeaStatus
    created_at: datetime
    responsible: MemberBrief | None


class AiIdeasRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)


class AiIdea(BaseModel):
    title: str
    format: str
    hook: str
    description: str
    caption: str
    hashtags: list[str]
    best_time: str
    why_it_works: str


class AiIdeasResponse(BaseModel):
    ideas: list[AiIdea]
