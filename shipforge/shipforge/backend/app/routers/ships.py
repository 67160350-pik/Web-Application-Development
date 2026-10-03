from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import calc, models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/ships", tags=["ships"])


def ship_to_out(ship: models.Ship) -> dict:
    return {
        "id": ship.id,
        "name": ship.name,
        "ship_type": ship.ship_type,
        "material_key": ship.material.key,
        "parts": [{"part_key": sp.part.key, "x": sp.x, "y": sp.y} for sp in ship.parts],
        "created_at": ship.created_at,
    }


def get_owned_ship(id: int, db: Session, user: models.User) -> models.Ship:
    ship = (
        db.query(models.Ship)
        .filter(models.Ship.id == id, models.Ship.user_id == user.id)
        .first()
    )
    if not ship:
        raise HTTPException(404, "Ship not found")
    return ship


@router.post("", response_model=schemas.ShipOut)
def create_ship(
    payload: schemas.ShipCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    material = db.query(models.Material).filter(models.Material.key == payload.material_key).first()
    if not material:
        raise HTTPException(400, "Unknown material")

    ship = models.Ship(
        user_id=user.id, name=payload.name, ship_type=payload.ship_type, material_id=material.id
    )
    db.add(ship)
    db.flush()

    for p in payload.parts:
        part = db.query(models.Part).filter(models.Part.key == p.part_key).first()
        if not part:
            continue
        db.add(models.ShipPart(ship_id=ship.id, part_id=part.id, x=p.x, y=p.y))

    db.commit()
    db.refresh(ship)
    return ship_to_out(ship)


@router.get("", response_model=List[schemas.ShipOut])
def list_ships(
    db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    ships = db.query(models.Ship).filter(models.Ship.user_id == user.id).all()
    return [ship_to_out(s) for s in ships]


@router.get("/{id}", response_model=schemas.ShipOut)
def get_ship(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    return ship_to_out(get_owned_ship(id, db, user))


@router.delete("/{id}")
def delete_ship(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    ship = get_owned_ship(id, db, user)
    db.delete(ship)
    db.commit()
    return {"message": "Deleted"}


@router.post("/{id}/inspect", response_model=schemas.StatsOut)
def inspect_ship(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    ship = get_owned_ship(id, db, user)
    items = [(sp.part, sp.x, sp.y) for sp in ship.parts]
    stats = calc.compute_stats(items, ship.material)
    overall, approved, issues = calc.run_inspection(stats)

    return {
        "weight": stats["weight"],
        "stability": stats["stability"],
        "buoyancy": stats["buoyancy"],
        "structural": stats["structural"],
        "engine_power": stats["engine_power"],
        "fuel_capacity": stats["fuel_capacity"],
        "cargo_capacity": stats["cargo_capacity"],
        "range": stats["range"],
        "engine_reliability": stats["engine_reliability"],
        "fuel_adequacy": stats["fuel_adequacy"],
        "safety_score": overall,
        "approved": approved,
        "issues": issues,
    }
