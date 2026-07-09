from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.security import CurrentMember, DbSession
from app.models.content import Post, VideoIdea
from app.schemas.content import (
    AiIdeasRequest,
    AiIdeasResponse,
    PostCreate,
    PostOut,
    PostUpdate,
    VideoIdeaCreate,
    VideoIdeaOut,
    VideoIdeaUpdate,
)
from app.services.ai import ai_configured, generate_content_ideas

router = APIRouter(prefix="/api/content", tags=["content"])


# ---------- Cronograma de postagens ----------

async def _get_post(db, post_id: int) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada")
    return post


@router.get("/posts", response_model=list[PostOut])
async def list_posts(
    _: CurrentMember, db: DbSession, start: date | None = None, end: date | None = None
):
    query = select(Post).order_by(Post.planned_date)
    if start is not None:
        query = query.where(Post.planned_date >= start)
    if end is not None:
        query = query.where(Post.planned_date <= end)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, _: CurrentMember, db: DbSession):
    post = Post(**payload.model_dump())
    db.add(post)
    await db.commit()
    return await _get_post(db, post.id)


@router.patch("/posts/{post_id}", response_model=PostOut)
async def update_post(post_id: int, payload: PostUpdate, _: CurrentMember, db: DbSession):
    post = await _get_post(db, post_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    await db.commit()
    return await _get_post(db, post_id)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, _: CurrentMember, db: DbSession):
    post = await _get_post(db, post_id)
    await db.delete(post)
    await db.commit()


# ---------- Ideias com IA (Claude) ----------

@router.post("/ai-ideas", response_model=AiIdeasResponse)
async def ai_ideas(payload: AiIdeasRequest, _: CurrentMember):
    """Gera ideias de conteúdo com a IA da Anthropic a partir de uma ideia inicial da banda."""
    if not ai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IA não configurada — defina ANTHROPIC_API_KEY no servidor.",
        )
    try:
        ideas = await generate_content_ideas(payload.prompt)
    except Exception as exc:  # noqa: BLE001 — erro da API externa vira 502 legível
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao gerar ideias com a IA: {exc}",
        ) from exc
    return AiIdeasResponse(ideas=ideas)


# ---------- Ideias de vídeo ----------

async def _get_idea(db, idea_id: int) -> VideoIdea:
    result = await db.execute(select(VideoIdea).where(VideoIdea.id == idea_id))
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    return idea


@router.get("/video-ideas", response_model=list[VideoIdeaOut])
async def list_ideas(_: CurrentMember, db: DbSession):
    result = await db.execute(select(VideoIdea).order_by(VideoIdea.created_at.desc()))
    return result.scalars().unique().all()


@router.post("/video-ideas", response_model=VideoIdeaOut, status_code=status.HTTP_201_CREATED)
async def create_idea(payload: VideoIdeaCreate, _: CurrentMember, db: DbSession):
    idea = VideoIdea(**payload.model_dump())
    db.add(idea)
    await db.commit()
    return await _get_idea(db, idea.id)


@router.patch("/video-ideas/{idea_id}", response_model=VideoIdeaOut)
async def update_idea(idea_id: int, payload: VideoIdeaUpdate, _: CurrentMember, db: DbSession):
    idea = await _get_idea(db, idea_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(idea, field, value)
    await db.commit()
    return await _get_idea(db, idea_id)


@router.delete("/video-ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(idea_id: int, _: CurrentMember, db: DbSession):
    idea = await _get_idea(db, idea_id)
    await db.delete(idea)
    await db.commit()
