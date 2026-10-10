from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(120))
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    ships = relationship("Ship", back_populates="owner", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(30), unique=True, nullable=False)
    label = Column(String(60), nullable=False)
    weight_mult = Column(Float, nullable=False)
    strength_mult = Column(Float, nullable=False)


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(30), unique=True, nullable=False)
    label = Column(String(60), nullable=False)
    base_weight = Column(Float, default=0)
    buoyancy = Column(Float, default=0)
    structural = Column(Float, default=0)
    stability = Column(Float, default=0)
    engine_power = Column(Float, default=0)
    fuel_capacity = Column(Float, default=0)
    cargo_capacity = Column(Float, default=0)
    safety = Column(Float, default=0)
    reliability = Column(Float, default=0)


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(60), default="Unnamed Vessel")
    ship_type = Column(String(30))
    material_id = Column(Integer, ForeignKey("materials.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="ships")
    material = relationship("Material")
    parts = relationship("ShipPart", back_populates="ship", cascade="all, delete-orphan")
    trials = relationship("SeaTrial", back_populates="ship", cascade="all, delete-orphan")


class ShipPart(Base):
    __tablename__ = "ship_parts"

    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

    ship = relationship("Ship", back_populates="parts")
    part = relationship("Part")


class ShipProject(Base):
    """Project / planning layer. Can wrap an existing Ship (game builder)
    OR stand alone as a pure planning project with no ship yet — ship_id
    is nullable so a project can be created straight from the guided
    Requirements Form before any 2D design exists.
    Additive table — does not alter ships/users/parts/materials."""
    __tablename__ = "ship_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ship_id = Column(Integer, ForeignKey("ships.id"), nullable=True)
    project_code = Column(String(20), unique=True, nullable=False)
    project_name = Column(String(120), nullable=False)
    client_name = Column(String(120), nullable=True)
    status = Column(String(20), default="PLANNING", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    start_date = Column(Date, nullable=True)
    target_date = Column(Date, nullable=True)

    # --- Planning / requirements fields (Professional Planning Platform) ---
    vessel_type = Column(String(60), nullable=True)
    intended_use = Column(String(120), nullable=True)
    operating_area = Column(String(120), nullable=True)
    requirements = Column(Text, nullable=True)  # JSON-encoded structured requirements
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # months

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User")
    ship = relationship("Ship")
    recommendations = relationship("DesignOption", back_populates="project", cascade="all, delete-orphan")


class DesignOption(Base):
    """One rule-based design recommendation generated for a ShipProject.
    Additive table — purely derived/advisory data."""
    __tablename__ = "design_options"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("ship_projects.id"), nullable=False)
    label = Column(String(60), nullable=False)          # e.g. "ตัวเลือก A — ประหยัด"
    length_m = Column(Float, nullable=True)
    beam_m = Column(Float, nullable=True)
    draft_m = Column(Float, nullable=True)
    material_key = Column(String(30), nullable=True)
    estimated_cost_min = Column(Float, nullable=True)
    estimated_cost_max = Column(Float, nullable=True)
    estimated_duration_months = Column(Integer, nullable=True)
    pros = Column(Text, nullable=True)   # JSON-encoded list[str]
    cons = Column(Text, nullable=True)   # JSON-encoded list[str]
    rationale = Column(Text, nullable=True)
    cost_breakdown = Column(Text, nullable=True)     # JSON-encoded list[{category,min,max}]
    timeline_phases = Column(Text, nullable=True)    # JSON-encoded list[{phase,months_min,months_max}]
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("ShipProject", back_populates="recommendations")


class Shipyard(Base):
    """Shipyard directory entry. SAMPLE DATA ONLY unless a verified source
    is wired up later — every row must be clearly labeled via `source` /
    `verified` so the UI never implies a real, confirmed business."""
    __tablename__ = "shipyards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    location = Column(String(120), nullable=True)
    vessel_types = Column(Text, nullable=True)     # JSON-encoded list[str] of SHIP_TYPES keys
    material_keys = Column(Text, nullable=True)    # JSON-encoded list[str] of material keys handled
    min_length_m = Column(Float, nullable=True)
    max_length_m = Column(Float, nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    contact = Column(String(120), nullable=True)
    source = Column(String(60), default="sample", nullable=False)   # "sample" | "verified"
    verified = Column(Integer, default=0, nullable=False)           # 0/1 boolean (MySQL-friendly)
    notes = Column(Text, nullable=True)


class ProjectShipyard(Base):
    """A shipyard the user shortlisted for a specific project."""
    __tablename__ = "project_shipyards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("ship_projects.id"), nullable=False)
    shipyard_id = Column(Integer, ForeignKey("shipyards.id"), nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("ShipProject")
    shipyard = relationship("Shipyard")


class SeaTrial(Base):
    __tablename__ = "sea_trials"

    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"), nullable=False)
    distance = Column(Float)
    sailing_time = Column(Integer)
    fuel_efficiency = Column(Float)
    safety_score = Column(Integer)
    hull_condition = Column(Float)
    grade = Column(String(2))
    created_at = Column(DateTime, server_default=func.now())

    ship = relationship("Ship", back_populates="trials")
