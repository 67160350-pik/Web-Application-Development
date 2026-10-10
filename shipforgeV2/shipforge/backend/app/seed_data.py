import json

from . import models

# SAMPLE / PLACEHOLDER DATA ONLY (§15). These are fictional entries used to
# exercise the Shipyard Discovery feature's data structure and matching
# logic — they are not real businesses, and every row is stored with
# source="sample" so the frontend must label it as unverified sample data.
# Names deliberately avoid resembling any specific real shipyard.
SHIPYARDS = [
    dict(
        name="อู่ตัวอย่าง A — อ่าวไทยตอนบน", location="สมุทรปราการ (ข้อมูลตัวอย่าง)",
        vessel_types=["fishing", "patrol", "speedboat"], material_keys=["steel", "aluminum"],
        min_length_m=6, max_length_m=35, budget_min=800000, budget_max=15000000,
        contact="ข้อมูลตัวอย่าง — ไม่ใช่เบอร์ติดต่อจริง",
        source="sample", verified=0,
        notes="รายการตัวอย่างสำหรับสาธิตการจับคู่อู่ต่อเรือ ยังไม่ผ่านการตรวจสอบความถูกต้อง",
    ),
    dict(
        name="อู่ตัวอย่าง B — ชายฝั่งอันดามัน", location="ภูเก็ต (ข้อมูลตัวอย่าง)",
        vessel_types=["cruise", "speedboat"], material_keys=["composite", "aluminum"],
        min_length_m=8, max_length_m=40, budget_min=2000000, budget_max=60000000,
        contact="ข้อมูลตัวอย่าง — ไม่ใช่เบอร์ติดต่อจริง",
        source="sample", verified=0,
        notes="รายการตัวอย่างสำหรับสาธิตการจับคู่อู่ต่อเรือ ยังไม่ผ่านการตรวจสอบความถูกต้อง",
    ),
    dict(
        name="อู่ตัวอย่าง C — ภาคใต้ตอนล่าง", location="สงขลา (ข้อมูลตัวอย่าง)",
        vessel_types=["cargo", "tanker"], material_keys=["steel", "hsteel"],
        min_length_m=25, max_length_m=180, budget_min=20000000, budget_max=400000000,
        contact="ข้อมูลตัวอย่าง — ไม่ใช่เบอร์ติดต่อจริง",
        source="sample", verified=0,
        notes="รายการตัวอย่างสำหรับสาธิตการจับคู่อู่ต่อเรือ ยังไม่ผ่านการตรวจสอบความถูกต้อง",
    ),
    dict(
        name="อู่ตัวอย่าง D — ภาคกลาง (แม่น้ำ/ชายฝั่ง)", location="สมุทรสาคร (ข้อมูลตัวอย่าง)",
        vessel_types=["fishing", "cargo", "cruise"], material_keys=["wood", "steel"],
        min_length_m=6, max_length_m=28, budget_min=500000, budget_max=12000000,
        contact="ข้อมูลตัวอย่าง — ไม่ใช่เบอร์ติดต่อจริง",
        source="sample", verified=0,
        notes="รายการตัวอย่างสำหรับสาธิตการจับคู่อู่ต่อเรือ ยังไม่ผ่านการตรวจสอบความถูกต้อง",
    ),
]

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
    if db.query(models.Shipyard).count() == 0:
        for y in SHIPYARDS:
            row = dict(y)
            row["vessel_types"] = json.dumps(row["vessel_types"], ensure_ascii=False)
            row["material_keys"] = json.dumps(row["material_keys"], ensure_ascii=False)
            db.add(models.Shipyard(**row))
    db.commit()
