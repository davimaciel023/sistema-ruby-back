from fastapi import APIRouter
from sqlalchemy import select

from app.core.security import CurrentMember, DbSession
from app.models.member import Member
from app.schemas.auth import MemberOut

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=list[MemberOut])
async def list_members(_: CurrentMember, db: DbSession):
    result = await db.execute(select(Member).where(Member.active).order_by(Member.id))
    return result.scalars().all()
