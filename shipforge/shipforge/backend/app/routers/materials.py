from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["materials"])


@router.get("/materials", response_model=List[schemas.MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(models.Material).all()
