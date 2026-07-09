from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import delete, select

from app.core.security import CurrentMember, DbSession
from app.models.repertoire import Repertoire, RepertoireSong, Song
from app.schemas.repertoire import (
    RepertoireCreate,
    RepertoireItemIn,
    RepertoireOut,
    RepertoireUpdate,
    SongCreate,
    SongOut,
    SongUpdate,
)
from app.services.pdf import build_combined_pdf, build_repertoire_pdf

router = APIRouter(prefix="/api/repertoire", tags=["repertoire"])


# ---------- Músicas ----------

async def _get_song(db, song_id: int) -> Song:
    result = await db.execute(select(Song).where(Song.id == song_id))
    song = result.scalar_one_or_none()
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Música não encontrada")
    return song


@router.get("/songs", response_model=list[SongOut])
async def list_songs(_: CurrentMember, db: DbSession):
    result = await db.execute(select(Song).order_by(Song.title))
    return result.scalars().all()


@router.post("/songs", response_model=SongOut, status_code=status.HTTP_201_CREATED)
async def create_song(payload: SongCreate, _: CurrentMember, db: DbSession):
    song = Song(**payload.model_dump())
    db.add(song)
    await db.commit()
    return song


@router.patch("/songs/{song_id}", response_model=SongOut)
async def update_song(song_id: int, payload: SongUpdate, _: CurrentMember, db: DbSession):
    song = await _get_song(db, song_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(song, field, value)
    await db.commit()
    return song


@router.delete("/songs/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_song(song_id: int, _: CurrentMember, db: DbSession):
    song = await _get_song(db, song_id)
    await db.delete(song)
    await db.commit()


# ---------- Repertórios ----------

def _total_seconds(rep: Repertoire) -> int:
    """RN09: tempo de show = soma das durações + intervalo entre músicas."""
    songs_total = sum(item.song.duration_seconds for item in rep.items)
    gaps = max(len(rep.items) - 1, 0) * rep.gap_seconds
    return songs_total + gaps


def _to_out(rep: Repertoire) -> RepertoireOut:
    out = RepertoireOut.model_validate(rep)
    out.total_seconds = _total_seconds(rep)
    return out


async def _get_repertoire(db, repertoire_id: int) -> Repertoire:
    result = await db.execute(select(Repertoire).where(Repertoire.id == repertoire_id))
    rep = result.scalar_one_or_none()
    if rep is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repertório não encontrado")
    return rep


async def _replace_items(db, rep: Repertoire, items: list[RepertoireItemIn]) -> None:
    await db.execute(delete(RepertoireSong).where(RepertoireSong.repertoire_id == rep.id))
    for position, item in enumerate(items, start=1):
        db.add(
            RepertoireSong(
                repertoire_id=rep.id,
                song_id=item.song_id,
                position=position,
                performed_key=item.performed_key,
            )
        )


@router.get("", response_model=list[RepertoireOut])
async def list_repertoires(_: CurrentMember, db: DbSession):
    result = await db.execute(select(Repertoire).order_by(Repertoire.created_at.desc()))
    return [_to_out(rep) for rep in result.scalars().unique().all()]


@router.post("", response_model=RepertoireOut, status_code=status.HTTP_201_CREATED)
async def create_repertoire(payload: RepertoireCreate, _: CurrentMember, db: DbSession):
    rep = Repertoire(**payload.model_dump(exclude={"items"}))
    db.add(rep)
    await db.flush()
    await _replace_items(db, rep, payload.items)
    await db.commit()
    return _to_out(await _get_repertoire(db, rep.id))


@router.patch("/{repertoire_id}", response_model=RepertoireOut)
async def update_repertoire(
    repertoire_id: int, payload: RepertoireUpdate, _: CurrentMember, db: DbSession
):
    rep = await _get_repertoire(db, repertoire_id)
    data = payload.model_dump(exclude_unset=True)
    items = data.pop("items", None)
    for field, value in data.items():
        setattr(rep, field, value)
    if items is not None:
        await _replace_items(db, rep, [RepertoireItemIn(**i) for i in items])
    await db.commit()
    return _to_out(await _get_repertoire(db, repertoire_id))


@router.delete("/{repertoire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repertoire(repertoire_id: int, _: CurrentMember, db: DbSession):
    rep = await _get_repertoire(db, repertoire_id)
    await db.delete(rep)
    await db.commit()


@router.get("/pdf-combined")
async def combined_pdf(ids: str, _: CurrentMember, db: DbSession):
    """PDF único juntando vários repertórios (blocos), ex.: ?ids=1,2,3."""
    try:
        id_list = [int(part) for part in ids.split(",") if part.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ids deve ser uma lista de números separados por vírgula",
        )
    if not id_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe ao menos um repertório",
        )
    blocks: list[tuple[Repertoire, int]] = []
    for repertoire_id in id_list:
        rep = await _get_repertoire(db, repertoire_id)
        blocks.append((rep, _total_seconds(rep)))
    grand_total = sum(total for _, total in blocks)
    pdf_bytes = build_combined_pdf(blocks, grand_total)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="repertorio-do-show.pdf"'},
    )


@router.get("/{repertoire_id}/pdf")
async def repertoire_pdf(repertoire_id: int, _: CurrentMember, db: DbSession):
    """RF25: PDF personalizado do repertório com a logo da banda."""
    rep = await _get_repertoire(db, repertoire_id)
    pdf_bytes = build_repertoire_pdf(rep, _total_seconds(rep))
    filename = f"repertorio-{rep.name.lower().replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
