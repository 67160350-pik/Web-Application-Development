from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, material_info
from ..database import get_db

router = APIRouter(prefix="/api", tags=["materials"])


@router.get("/materials", response_model=List[schemas.MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(models.Material).all()


@router.get("/materials/info", response_model=List[schemas.MaterialInfoOut])
def list_materials_info(db: Session = Depends(get_db)):
    """§12 — transparent material trade-off reference (cost, weight,
    corrosion, maintenance, durability, fabrication). General engineering
    guidance, not sourced/dated market pricing."""
    out = []
    for m in db.query(models.Material).all():
        info = material_info.get_material_info(m.key)
        out.append({"key": m.key, **info})
    return out
