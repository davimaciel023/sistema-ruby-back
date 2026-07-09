from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.security import CurrentMember, DbSession
from app.models.study import StudyMaterial
from app.schemas.study import MaterialCreate, MaterialOut, MaterialUpdate

router = APIRouter(prefix="/api/study", tags=["study"])


async def _get_material(db, material_id: int) -> StudyMaterial:
    result = await db.execute(select(StudyMaterial).where(StudyMaterial.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")
    return material


@router.get("/materials", response_model=list[MaterialOut])
async def list_materials(_: CurrentMember, db: DbSession, owner_id: int | None = None):
    query = select(StudyMaterial).order_by(StudyMaterial.created_at.desc())
    if owner_id is not None:
        query = query.where(StudyMaterial.owner_id == owner_id)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("/materials", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def create_material(payload: MaterialCreate, _: CurrentMember, db: DbSession):
    material = StudyMaterial(**payload.model_dump())
    db.add(material)
    await db.commit()
    return await _get_material(db, material.id)


@router.patch("/materials/{material_id}", response_model=MaterialOut)
async def update_material(material_id: int, payload: MaterialUpdate, _: CurrentMember, db: DbSession):
    material = await _get_material(db, material_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(material, field, value)
    await db.commit()
    return await _get_material(db, material_id)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: int, _: CurrentMember, db: DbSession):
    material = await _get_material(db, material_id)
    await db.delete(material)
    await db.commit()
