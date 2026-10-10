import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from .projects import get_owned_project

router = APIRouter(prefix="/api", tags=["shipyards"])


def _loads(raw):
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return []


def _shipyard_to_out(s: models.Shipyard, match_reasons=None) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "location": s.location,
        "vessel_types": _loads(s.vessel_types),
        "material_keys": _loads(s.material_keys),
        "min_length_m": s.min_length_m,
        "max_length_m": s.max_length_m,
        "budget_min": s.budget_min,
        "budget_max": s.budget_max,
        "contact": s.contact,
        "source": s.source,
        "verified": bool(s.verified),
        "notes": s.notes,
        "match_reasons": match_reasons or [],
    }


@router.get("/shipyards", response_model=List[schemas.ShipyardOut])
def list_shipyards(
    vessel_type: Optional[str] = Query(None),
    budget_max: Optional[float] = Query(None),
    length_m: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    """§15 Shipyard Discovery. SAMPLE DATA ONLY — every row is labeled
    source='sample' unless a verified source is wired up later. Results are
    sorted by how many criteria matched; nothing is excluded outright so a
    user can still see near-misses with their mismatched reasons noted."""
    rows = db.query(models.Shipyard).all()
    scored = []
    for s in rows:
        reasons = []
        score = 0
        vtypes = _loads(s.vessel_types)
        if vessel_type:
            if vessel_type in vtypes:
                reasons.append("รองรับประเภทเรือที่คุณระบุ")
                score += 2
        if budget_max is not None and s.budget_min is not None:
            if s.budget_min <= budget_max:
                reasons.append("ช่วงงบประมาณสอดคล้องกับโครงการ")
                score += 1
        if length_m is not None and s.min_length_m is not None and s.max_length_m is not None:
            if s.min_length_m <= length_m <= s.max_length_m:
                reasons.append("รองรับขนาดความยาวเรือที่ประเมินไว้")
                score += 1
        scored.append((score, s, reasons))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [_shipyard_to_out(s, reasons) for _, s, reasons in scored]


@router.get("/projects/{id}/shipyards", response_model=List[schemas.ShortlistOut])
def list_shortlist(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    project = get_owned_project(id, db, user)
    rows = (
        db.query(models.ProjectShipyard)
        .filter(models.ProjectShipyard.project_id == project.id)
        .order_by(models.ProjectShipyard.id)
        .all()
    )
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "shipyard": _shipyard_to_out(r.shipyard),
            "note": r.note,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/projects/{id}/shipyards", response_model=schemas.ShortlistOut)
def add_to_shortlist(
    id: int,
    payload: schemas.ShortlistIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    project = get_owned_project(id, db, user)
    shipyard = db.query(models.Shipyard).filter(models.Shipyard.id == payload.shipyard_id).first()
    if not shipyard:
        raise HTTPException(404, "Shipyard not found")
    existing = (
        db.query(models.ProjectShipyard)
        .filter(models.ProjectShipyard.project_id == project.id, models.ProjectShipyard.shipyard_id == shipyard.id)
        .first()
    )
    if existing:
        raise HTTPException(400, "Shipyard already shortlisted for this project")
    row = models.ProjectShipyard(project_id=project.id, shipyard_id=shipyard.id, note=payload.note)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "project_id": row.project_id,
        "shipyard": _shipyard_to_out(row.shipyard),
        "note": row.note,
        "created_at": row.created_at,
    }


@router.delete("/projects/{id}/shipyards/{shortlist_id}")
def remove_from_shortlist(
    id: int,
    shortlist_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    project = get_owned_project(id, db, user)
    row = (
        db.query(models.ProjectShipyard)
        .filter(models.ProjectShipyard.id == shortlist_id, models.ProjectShipyard.project_id == project.id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
