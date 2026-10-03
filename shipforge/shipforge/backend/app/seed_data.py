from . import models

PARTS = [
    dict(key="hull", label="Hull", base_weight=400, buoyancy=60, structural=18),
    dict(key="engine", label="Engine", base_weight=150, engine_power=120),
    dict(key="fuelTank", label="Fuel Tank", base_weight=60, fuel_capacity=520),
    dict(key="cargoHold", label="Cargo Hold", base_weight=80, cargo_capacity=300),
    dict(key="bridge", label="Bridge", base_weight=40, safety=10, structural=5),
    dict(key="stabilizer", label="Stabilizer", base_weight=50, stability=26),
    dict(key="powerSys", label="Power System", base_weight=45, reliability=22, safety=5),
    dict(key="safetySys", label="Safety System", base_weight=30, safety=26),
]

MATERIALS = [
    dict(key="wood", label="Wood", weight_mult=0.55, strength_mult=0.45),
    dict(key="aluminum", label="Aluminum", weight_mult=0.7, strength_mult=0.7),
    dict(key="steel", label="Steel", weight_mult=1.0, strength_mult=1.0),
    dict(key="hsteel", label="High-strength Steel", weight_mult=1.25, strength_mult=1.45),
    dict(key="composite", label="Composite", weight_mult=0.5, strength_mult=1.15),
]


def seed(db):
    if db.query(models.Material).count() == 0:
        for m in MATERIALS:
            db.add(models.Material(**m))
    if db.query(models.Part).count() == 0:
        for p in PARTS:
            db.add(models.Part(**p))
    db.commit()
