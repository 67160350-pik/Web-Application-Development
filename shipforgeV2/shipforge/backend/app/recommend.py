"""Rule-based Design Recommendation Engine.

IMPORTANT: this is a transparent, deterministic rule-based estimator —
NOT machine learning and NOT a certified naval-architecture calculation.
Every number here is a rough order-of-magnitude planning estimate meant
to help a user compare directions before engaging a naval architect /
shipyard. All formulas are simple, explainable multipliers so the
rationale text can always say exactly why a number came out the way it
did (spec requirement: engine must be explainable, never a black box).
"""
import json
from typing import List, Optional

from . import models

# Typical length/beam ratio and beam/draft ratio used for the preliminary
# hull-sizing estimate (rough naval-architecture rules of thumb).
LB_RATIO = 5.5
BD_RATIO = 0.35

# Baseline length (m) by vessel type when no capacity figure is given,
# and how length scales with the requested capacity.
VESSEL_BASELINE = {
    "fishing":   dict(base_len=18, per_crew=1.2, per_cargo=0.08),
    "cruise":    dict(base_len=22, per_crew=0.6, per_cargo=0.0, per_passenger=0.35),
    "cargo":     dict(base_len=30, per_crew=0.8, per_cargo=0.18),
    "tanker":    dict(base_len=40, per_crew=0.8, per_cargo=0.15),
    "patrol":    dict(base_len=20, per_crew=1.0, per_cargo=0.0),
    "speedboat": dict(base_len=10, per_crew=0.8, per_cargo=0.0),
}
DEFAULT_BASELINE = dict(base_len=20, per_crew=1.0, per_cargo=0.1, per_passenger=0.3)

# Material tiers: (material_key, cost per m^2 of hull footprint in THB,
# relative build-speed multiplier, short Thai pros/cons)
TIERS = [
    dict(
        label="ประหยัด (Economy)",
        material_key="wood",
        cost_per_m2=28000,
        duration_mult=0.85,
        pros=["ต้นทุนวัสดุต่ำที่สุด", "ซ่อมบำรุงง่ายในอู่ท้องถิ่น", "เหมาะงบประมาณจำกัด"],
        cons=["อายุการใช้งานโครงสร้างสั้นกว่า", "ทนทานต่อสภาพทะเลหนักได้น้อยกว่า"],
    ),
    dict(
        label="สมดุล (Balanced)",
        material_key="steel",
        cost_per_m2=46000,
        duration_mult=1.0,
        pros=["สมดุลระหว่างต้นทุนและความแข็งแรง", "หาช่างและอู่ต่อเรือที่ชำนาญได้ทั่วไป", "เป็นมาตรฐานอุตสาหกรรม"],
        cons=["น้ำหนักตัวเรือมากกว่าวัสดุทางเลือก", "ต้องมีการป้องกันสนิมต่อเนื่อง"],
    ),
    dict(
        label="สมรรถนะสูง (Premium)",
        material_key="hsteel",
        cost_per_m2=72000,
        duration_mult=1.2,
        pros=["ความแข็งแรงต่อน้ำหนักสูงสุด", "อายุการใช้งานยาวนาน", "รองรับการใช้งานหนัก/ระยะไกล"],
        cons=["ต้นทุนวัสดุและแรงงานสูงสุด", "ต้องใช้ช่างเทคนิคเฉพาะทาง ระยะเวลาสร้างนานขึ้น"],
    ),
]


# Cost category shares (§13) — fixed proportions of the total estimate.
# These are planning-level allocation ratios commonly used for rough order-
# of-magnitude small-craft budgeting, not sourced market data; they always
# sum to 1.0 so the category breakdown reconciles exactly with the total.
COST_CATEGORIES = [
    ("hull_structure",   "โครงสร้างและตัวเรือหลัก",            0.32),
    ("materials_fab",    "วัสดุและการขึ้นรูป",                  0.14),
    ("propulsion",       "ระบบขับเคลื่อน",                      0.16),
    ("electrical_mech",  "ระบบไฟฟ้าและเครื่องกล",                0.10),
    ("nav_safety",       "อุปกรณ์เดินเรือและความปลอดภัย",        0.07),
    ("labor",            "ค่าแรง",                              0.10),
    ("finishing",        "งานตกแต่งและติดตั้งภายใน",             0.06),
    ("inspection_commissioning", "การตรวจสอบและทดสอบก่อนส่งมอบ",  0.03),
    ("contingency",      "เงินสำรองฉุกเฉิน",                     0.02),
]
assert abs(sum(c[2] for c in COST_CATEGORIES) - 1.0) < 1e-9

# Construction timeline phases (§14) — share of total estimated duration.
TIMELINE_PHASES = [
    ("requirements_concept", "ข้อกำหนดและแนวคิดการออกแบบ", 0.08),
    ("prelim_engineering",   "วิศวกรรมเบื้องต้น",            0.10),
    ("detailed_design",      "ออกแบบรายละเอียดและทบทวนทางวิศวกรรม", 0.12),
    ("procurement",          "จัดหาวัสดุและอุปกรณ์",         0.15),
    ("hull_fabrication",     "ขึ้นรูปตัวเรือ",               0.28),
    ("equipment_install",    "ติดตั้งอุปกรณ์",               0.15),
    ("inspection_finishing", "ตรวจสอบและงานตกแต่ง",          0.07),
    ("testing_commissioning","ทดสอบและส่งมอบ",               0.05),
]
assert abs(sum(p[2] for p in TIMELINE_PHASES) - 1.0) < 1e-9


def _cost_breakdown(cost_min: float, cost_max: float) -> List[dict]:
    return [
        dict(category=key, label=label, cost_min=round(cost_min * share, -2), cost_max=round(cost_max * share, -2))
        for key, label, share in COST_CATEGORIES
    ]


def _timeline_phases(duration_months: int) -> List[dict]:
    rows = []
    for key, label, share in TIMELINE_PHASES:
        months = duration_months * share
        lo = max(0.5, round(months * 0.85, 1))
        hi = round(months * 1.2, 1)
        rows.append(dict(phase=key, label=label, months_min=lo, months_max=hi))
    return rows


def _hull_length(vessel_type: Optional[str], crew_size, cargo_tons, passengers) -> float:
    bl = VESSEL_BASELINE.get(vessel_type or "", DEFAULT_BASELINE)
    length = bl.get("base_len", 20)
    if crew_size:
        length += bl.get("per_crew", 0.8) * float(crew_size)
    if cargo_tons:
        length += bl.get("per_cargo", 0.1) * float(cargo_tons)
    if passengers:
        length += bl.get("per_passenger", 0.3) * float(passengers)
    return round(max(6.0, min(length, 260.0)), 1)


def generate_recommendations(project: models.ShipProject) -> List[dict]:
    """Return a list of dict rows ready to become DesignOption records."""
    req = {}
    if project.requirements:
        try:
            req = json.loads(project.requirements)
        except (TypeError, ValueError):
            req = {}

    vessel_type = project.vessel_type or req.get("vessel_type")
    crew_size = req.get("crew_size")
    cargo_tons = req.get("cargo_capacity_tons")
    passengers = req.get("passenger_capacity")
    desired_speed = req.get("desired_speed_knots")

    length = _hull_length(vessel_type, crew_size, cargo_tons, passengers)
    beam = round(length / LB_RATIO, 2)
    draft = round(beam * BD_RATIO, 2)
    footprint_m2 = round(length * beam, 1)

    budget_min = project.budget_min
    budget_max = project.budget_max

    options = []
    for tier in TIERS:
        base_cost = footprint_m2 * tier["cost_per_m2"]
        cost_min = round(base_cost * 0.9, -3)
        cost_max = round(base_cost * 1.25, -3)

        base_months = 4 + length / 12
        duration_months = max(2, round(base_months * tier["duration_mult"]))

        pros = list(tier["pros"])
        cons = list(tier["cons"])
        if desired_speed and vessel_type == "speedboat" and tier["material_key"] in ("hsteel", "composite"):
            pros.append("น้ำหนักเบาเหมาะกับการทำความเร็วสูงตามที่ต้องการ")

        within_budget = True
        if budget_min is not None and cost_max < budget_min:
            within_budget = True  # cheaper than minimum is not a problem
        if budget_max is not None and cost_min > budget_max:
            within_budget = False
            cons.append("ต้นทุนประเมินเกินงบประมาณสูงสุดที่ระบุไว้")

        rationale = (
            f"ประเมินจากขนาดตัวเรือเบื้องต้น {length} ม. (กว้าง {beam} ม. / กินน้ำลึก {draft} ม.) "
            f"พื้นที่ตัวถังโดยประมาณ {footprint_m2} ตร.ม. × ต้นทุนวัสดุ {tier['label']} "
            f"({tier['cost_per_m2']:,.0f} บาท/ตร.ม.) นี่เป็นการประมาณการเบื้องต้นสำหรับวางแผน "
            f"ยังไม่ผ่านการรับรองทางวิศวกรรมเรือ ควรให้วิศวกรต่อเรือตรวจสอบก่อนตัดสินใจจริง"
        )

        options.append(dict(
            label=tier["label"],
            length_m=length,
            beam_m=beam,
            draft_m=draft,
            material_key=tier["material_key"],
            estimated_cost_min=cost_min,
            estimated_cost_max=cost_max,
            estimated_duration_months=duration_months,
            pros=pros,
            cons=cons,
            rationale=rationale,
            cost_breakdown=_cost_breakdown(cost_min, cost_max),
            timeline_phases=_timeline_phases(duration_months),
        ))

    return options
