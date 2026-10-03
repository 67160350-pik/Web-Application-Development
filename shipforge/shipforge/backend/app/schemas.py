import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    label: str
    weight_mult: float
    strength_mult: float


class PartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    label: str
    base_weight: float
    buoyancy: float
    structural: float
    stability: float
    engine_power: float
    fuel_capacity: float
    cargo_capacity: float
    safety: float
    reliability: float


class ShipPartIn(BaseModel):
    part_key: str
    x: int
    y: int


class ShipCreate(BaseModel):
    name: str = "Unnamed Vessel"
    ship_type: str
    material_key: str
    parts: List[ShipPartIn] = []


class ShipPartOut(BaseModel):
    part_key: str
    x: int
    y: int


class ShipOut(BaseModel):
    id: int
    name: str
    ship_type: str
    material_key: str
    parts: List[ShipPartOut]
    created_at: datetime.datetime


class StatsOut(BaseModel):
    weight: float
    stability: float
    buoyancy: float
    structural: float
    engine_power: float
    fuel_capacity: float
    cargo_capacity: float
    range: float
    engine_reliability: float
    fuel_adequacy: float
    safety_score: int
    approved: bool
    issues: List[str]


class TrialCreate(BaseModel):
    distance: float
    sailing_time: int
    fuel_efficiency: float
    safety_score: int
    hull_condition: float
    grade: str


class TrialOut(TrialCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
