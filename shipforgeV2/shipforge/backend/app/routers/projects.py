import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from .. import recommend

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _parse_requirements(raw: Optional[str]) -> Optional[dict]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def project_to_out(p: models.ShipProject) -> dict:
    return {
        "id": p.id,
        "project_code": p.project_code,
        "ship_id": p.ship_id,
        "ship_name": p.ship.name if p.ship else None,
        "ship_type": p.ship.ship_type if p.ship else None,
        "project_name": p.project_name,
        "client_name": p.client_name,
        "status": p.status,
        "progress": p.progress,
        "start_date": p.start_date,
        "target_date": p.target_date,
        "vessel_type": p.vessel_type,
        "intended_use": p.intended_use,
        "operating_area": p.operating_area,
        "requirements": _parse_requirements(p.requirements),
        "budget_min": p.budget_min,
        "budget_max": p.budget_max,
        "estimated_duration": p.estimated_duration,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def get_owned_project(id: int, db: Session, user: models.User) -> models.ShipProject:
    p = (
        db.query(models.ShipProject)
        .filter(models.ShipProject.id == id, models.ShipProject.user_id == user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Project not found")
    return p


def _apply_requirements(project: models.ShipProject, payload) -> None:
    """Store the structured RequirementsIn (if any) as JSON, and mirror its
    summary fields onto the project's own columns so they're queryable —
    an explicit top-level field on the payload always wins over the value
    nested inside `requirements`."""
    req = payload.requirements
    if req is not None:
        project.requirements = json.dumps(req.model_dump(exclude_none=True), ensure_ascii=False)

    vessel_type = payload.vessel_type if payload.vessel_type is not None else (req.vessel_type if req else None)
    if vessel_type is not None:
        project.vessel_type = vessel_type

    intended_use = payload.intended_use if payload.intended_use is not None else (req.intended_use if req else None)
    if intended_use is not None:
        project.intended_use = intended_use

    operating_area = payload.operating_area if payload.operating_area is not None else (req.operating_area if req else None)
    if operating_area is not None:
        project.operating_area = operating_area

    budget_min = payload.budget_min if payload.budget_min is not None else (req.budget_min if req else None)
    if budget_min is not None:
        project.budget_min = budget_min

    budget_max = payload.budget_max if payload.budget_max is not None else (req.budget_max if req else None)
    if budget_max is not None:
        project.budget_max = budget_max

    estimated_duration = payload.estimated_duration if payload.estimated_duration is not None else (
        req.estimated_duration if req else None
    )
    if estimated_duration is not None:
        project.estimated_duration = estimated_duration


@router.post("", response_model=schemas.ProjectOut)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    # A project no longer requires a completed ship — ship_id is optional
    # so a project can be created straight from the Requirements Form.
    ship = None
    if payload.ship_id is not None:
        ship = (
            db.query(models.Ship)
            .filter(models.Ship.id == payload.ship_id, models.Ship.user_id == user.id)
            .first()
        )
        if not ship:
            raise HTTPException(404, "Ship not found")
    if payload.status not in schemas.PROJECT_STATUSES:
        raise HTTPException(400, "Invalid status")

    project = models.ShipProject(
        user_id=user.id,
        ship_id=ship.id if ship else None,
        project_code="TEMP",
        project_name=payload.project_name,
        client_name=payload.client_name,
        status=payload.status,
        progress=max(0, min(100, payload.progress)),
        start_date=payload.start_date,
        target_date=payload.target_date,
    )
    _apply_requirements(project, payload)
    db.add(project)
    db.flush()
    project.project_code = f"SF-{project.id:04d}"
    db.commit()
    db.refresh(project)
    return project_to_out(project)


@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(
    db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    projects = db.query(models.ShipProject).filter(models.ShipProject.user_id == user.id).all()
    return [project_to_out(p) for p in projects]


@router.get("/{id}", response_model=schemas.ProjectOut)
def get_project(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    return project_to_out(get_owned_project(id, db, user))


@router.put("/{id}", response_model=schemas.ProjectOut)
def update_project(
    id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    project = get_owned_project(id, db, user)
    if payload.ship_id is not None:
        ship = (
            db.query(models.Ship)
            .filter(models.Ship.id == payload.ship_id, models.Ship.user_id == user.id)
            .first()
        )
        if not ship:
            raise HTTPException(404, "Ship not found")
        project.ship_id = ship.id
    if payload.project_name is not None:
        project.project_name = payload.project_name
    if payload.client_name is not None:
        project.client_name = payload.client_name
    if payload.status is not None:
        if payload.status not in schemas.PROJECT_STATUSES:
            raise HTTPException(400, "Invalid status")
        project.status = payload.status
    if payload.progress is not None:
        project.progress = max(0, min(100, payload.progress))
    if payload.start_date is not None:
        project.start_date = payload.start_date
    if payload.target_date is not None:
        project.target_date = payload.target_date
    _apply_requirements(project, payload)
    db.commit()
    db.refresh(project)
    return project_to_out(project)


@router.delete("/{id}")
def delete_project(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    project = get_owned_project(id, db, user)
    db.delete(project)
    db.commit()
    return {"message": "Deleted"}


def _option_to_out(o: models.DesignOption) -> dict:
    def _loads(raw):
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return []

    return {
        "id": o.id,
        "project_id": o.project_id,
        "label": o.label,
        "length_m": o.length_m,
        "beam_m": o.beam_m,
        "draft_m": o.draft_m,
        "material_key": o.material_key,
        "estimated_cost_min": o.estimated_cost_min,
        "estimated_cost_max": o.estimated_cost_max,
        "estimated_duration_months": o.estimated_duration_months,
        "pros": _loads(o.pros),
        "cons": _loads(o.cons),
        "rationale": o.rationale,
        "cost_breakdown": _loads(o.cost_breakdown),
        "timeline_phases": _loads(o.timeline_phases),
        "created_at": o.created_at,
    }


@router.post("/{id}/recommendations", response_model=List[schemas.DesignOptionOut])
def generate_recommendations(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    """Rule-based, explainable design recommendations — not ML, not a
    certified engineering calculation. Replaces any previously generated
    options for this project with a fresh set."""
    project = get_owned_project(id, db, user)

    db.query(models.DesignOption).filter(models.DesignOption.project_id == project.id).delete()

    rows = recommend.generate_recommendations(project)
    created = []
    for row in rows:
        option = models.DesignOption(
            project_id=project.id,
            label=row["label"],
            length_m=row["length_m"],
            beam_m=row["beam_m"],
            draft_m=row["draft_m"],
            material_key=row["material_key"],
            estimated_cost_min=row["estimated_cost_min"],
            estimated_cost_max=row["estimated_cost_max"],
            estimated_duration_months=row["estimated_duration_months"],
            pros=json.dumps(row["pros"], ensure_ascii=False),
            cons=json.dumps(row["cons"], ensure_ascii=False),
            rationale=row["rationale"],
            cost_breakdown=json.dumps(row["cost_breakdown"], ensure_ascii=False),
            timeline_phases=json.dumps(row["timeline_phases"], ensure_ascii=False),
        )
        db.add(option)
        created.append(option)
    db.commit()
    for o in created:
        db.refresh(o)
    return [_option_to_out(o) for o in created]


@router.get("/{id}/recommendations", response_model=List[schemas.DesignOptionOut])
def list_recommendations(
    id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)
):
    project = get_owned_project(id, db, user)
    rows = (
        db.query(models.DesignOption)
        .filter(models.DesignOption.project_id == project.id)
        .order_by(models.DesignOption.id)
        .all()
    )
    return [_option_to_out(o) for o in rows]
