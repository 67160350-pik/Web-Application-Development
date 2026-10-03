from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
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
