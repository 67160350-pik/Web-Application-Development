from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from .ships import get_owned_ship

router = APIRouter(prefix="/api/ships", tags=["trials"])


@router.post("/{id}/sea-trial", response_model=schemas.TrialOut)
def save_trial(
    id: int,
    payload: schemas.TrialCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    ship = get_owned_ship(id, db, user)
    trial = models.SeaTrial(ship_id=ship.id, **payload.model_dump())
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


@router.get("/{id}/trials", response_model=List[schemas.TrialOut])
def list_trials(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    ship = get_owned_ship(id, db, user)
    return ship.trials
