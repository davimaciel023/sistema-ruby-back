"""Seed inicial: cria os 3 integrantes da banda se ainda não existirem."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.member import Member

logger = logging.getLogger(__name__)

MEMBERS = [
    {"name": "Davi Maciel", "role": "Sanfoneiro", "email": "davi@forroruby.com", "avatar_color": "#b00020"},
    {"name": "Nágilla Silva", "role": "Cantora", "email": "nagilla@forroruby.com", "avatar_color": "#7b1fa2"},
    {"name": "Luid Ferreira", "role": "Tecladista e cantor", "email": "luid@forroruby.com", "avatar_color": "#1565c0"},
]


async def seed_members(db: AsyncSession) -> None:
    result = await db.execute(select(Member))
    if result.scalars().first() is not None:
        return
    hashed = hash_password(settings.seed_default_password)
    for data in MEMBERS:
        db.add(Member(**data, hashed_password=hashed))
    await db.commit()
    logger.info("Seed: 3 integrantes criados com a senha padrão inicial")
