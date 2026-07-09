from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MemberBrief(ORMModel):
    id: int
    name: str
    role: str
    avatar_color: str
