from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["parts"])


@router.get("/parts", response_model=List[schemas.PartOut])
def list_parts(search: str = "", db: Session = Depends(get_db)):
    q = db.query(models.Part)
    if search:
        q = q.filter(models.Part.label.ilike(f"%{search}%"))
    return q.all()
