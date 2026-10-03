from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(security.get_current_user)):
    return user


@router.get("/users/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    u = db.get(models.User, id)
    if not u:
        raise HTTPException(404, "User not found")
    return u


@router.get("/users")
def list_users(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    q = db.query(models.User)
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [schemas.UserOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.put("/users/{id}", response_model=schemas.UserOut)
def update_user(
    id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current: models.User = Depends(security.get_current_user),
):
    if current.id != id:
        raise HTTPException(403, "Not allowed")
    u = db.get(models.User, id)
    if payload.email is not None:
        u.email = payload.email
    if payload.full_name is not None:
        u.full_name = payload.full_name
    db.commit()
    db.refresh(u)
    return u


@router.delete("/users/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current: models.User = Depends(security.get_current_user),
):
    if current.id != id:
        raise HTTPException(403, "Not allowed")
    u = db.get(models.User, id)
    db.delete(u)
    db.commit()
    return {"message": "Deleted"}


@router.get("/check-username/{name}")
def check_username(name: str, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.username == name).first() is not None
    return {"available": not exists}
