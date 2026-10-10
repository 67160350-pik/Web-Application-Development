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
    wrong_zone_count: int
    unsupported: int
    disconnected_engines: int
    structural_stress: int
    safety_score: int
    approved: bool
    issues: List[str]


PROJECT_STATUSES = ["PLANNING", "DESIGN", "CONSTRUCTION", "INSPECTION", "SEA_TRIAL", "COMPLETED", "ON_HOLD"]


class RequirementsIn(BaseModel):
    """Structured answers from the guided Requirements Form.
    Stored JSON-encoded in ShipProject.requirements; the individual
    summary fields are also mirrored onto their own columns for querying."""
    vessel_type: Optional[str] = None
    intended_use: Optional[str] = None
    operating_area: Optional[str] = None
    passenger_capacity: Optional[int] = None
    cargo_capacity_tons: Optional[float] = None
    desired_speed_knots: Optional[float] = None
    crew_size: Optional[int] = None
    notes: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    estimated_duration: Optional[int] = None


class ProjectCreate(BaseModel):
    ship_id: Optional[int] = None
    project_name: str
    client_name: Optional[str] = None
    status: str = "PLANNING"
    progress: int = 0
    start_date: Optional[datetime.date] = None
    target_date: Optional[datetime.date] = None
    vessel_type: Optional[str] = None
    intended_use: Optional[str] = None
    operating_area: Optional[str] = None
    requirements: Optional[RequirementsIn] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    estimated_duration: Optional[int] = None


class ProjectUpdate(BaseModel):
    ship_id: Optional[int] = None
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    start_date: Optional[datetime.date] = None
    target_date: Optional[datetime.date] = None
    vessel_type: Optional[str] = None
    intended_use: Optional[str] = None
    operating_area: Optional[str] = None
    requirements: Optional[RequirementsIn] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    estimated_duration: Optional[int] = None


class ProjectOut(BaseModel):
    id: int
    project_code: str
    ship_id: Optional[int] = None
    ship_name: Optional[str] = None
    ship_type: Optional[str] = None
    project_name: str
    client_name: Optional[str] = None
    status: str
    progress: int
    start_date: Optional[datetime.date] = None
    target_date: Optional[datetime.date] = None
    vessel_type: Optional[str] = None
    intended_use: Optional[str] = None
    operating_area: Optional[str] = None
    requirements: Optional[RequirementsIn] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    estimated_duration: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DesignOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    label: str
    length_m: Optional[float] = None
    beam_m: Optional[float] = None
    draft_m: Optional[float] = None
    material_key: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    estimated_duration_months: Optional[int] = None
    pros: List[str] = []
    cons: List[str] = []
    rationale: Optional[str] = None
    cost_breakdown: List[dict] = []
    timeline_phases: List[dict] = []
    created_at: datetime.datetime


class MaterialInfoOut(BaseModel):
    key: str
    label: str
    cost: str
    weight: str
    corrosion: str
    maintenance: str
    durability: str
    fabrication: str


class ShipyardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    location: Optional[str] = None
    vessel_types: List[str] = []
    material_keys: List[str] = []
    min_length_m: Optional[float] = None
    max_length_m: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    contact: Optional[str] = None
    source: str = "sample"
    verified: bool = False
    notes: Optional[str] = None
    match_reasons: List[str] = []


class ShortlistIn(BaseModel):
    shipyard_id: int
    note: Optional[str] = None


class ShortlistOut(BaseModel):
    id: int
    project_id: int
    shipyard: ShipyardOut
    note: Optional[str] = None
    created_at: datetime.datetime


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
