def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# Zone each part type belongs to. Columns 0-9: 0-1 bow, 2-4 cargo, 5-7 fuel,
# 8-9 engine. Row 4 (bottom) = keel. Mirrors PART_META in the frontend JS.
PART_ZONE = {
    "hull": "any",
    "engine": "engine",
    "fuelTank": "fuel",
    "cargoHold": "cargo",
    "bridge": "bow",
    "stabilizer": "keel",
    "powerSys": "engine",
    "safetySys": "any",
}
NEEDS_SUPPORT = {"fuelTank", "cargoHold"}
ENGINE_CONNECT_TO = "fuelTank"
ENGINE_MAX_DIST = 4
SUPPORT_DIST = 4


def zone_matches(zone, x, y):
    if zone == "any":
        return True
    if zone == "keel":
        return y == 4
    if zone == "bow":
        return x <= 1
    if zone == "cargo":
        return 2 <= x <= 4
    if zone == "fuel":
        return 5 <= x <= 7
    if zone == "engine":
        return x >= 8
    return True


def compute_stats(items, material):
    """items: list of (Part, x, y) tuples. material: Material row.
    Mirrors analyzeShip() in the frontend exactly, including zone
    correctness, engine<->fuel connection distance, and stabilizer
    support for heavy parts."""
    weight = 0.0
    buoyancy = 0.0
    structural = 0.0
    stability = 52.0
    engine_power = 0.0
    fuel_capacity = 0.0
    cargo_capacity = 0.0
    safety = 0.0
    reliability = 0.0
    hull_count = 0
    engine_count = 0

    zone_ok = {}
    engines = []
    fuel_tanks = []
    stabilizers = []
    heavy_parts = []

    for part, x, y in items:
        zone = PART_ZONE.get(part.key, "any")
        ok = zone_matches(zone, x, y)
        zone_ok[id(part), x, y] = ok
        mult = 1.0 if ok else 0.55

        w = part.base_weight * material.weight_mult
        weight += w
        if part.buoyancy:
            buoyancy += part.buoyancy * mult
            hull_count += 1
        if part.structural:
            structural += part.structural * material.strength_mult * mult
        if part.stability:
            stability += part.stability * mult
        if part.engine_power:
            engine_power += part.engine_power * mult
            engine_count += 1
            engines.append((part, x, y, ok))
        if part.fuel_capacity:
            fuel_capacity += part.fuel_capacity * mult
            fuel_tanks.append((part, x, y))
        if part.cargo_capacity:
            cargo_capacity += part.cargo_capacity * mult
        if part.safety:
            safety += part.safety * mult
        if part.reliability:
            reliability += part.reliability * mult
        if part.key == "stabilizer":
            stabilizers.append((part, x, y))
        if part.key in NEEDS_SUPPORT:
            heavy_parts.append((part, x, y, ok))

    balance_penalty = 0.0
    if items:
        avg_x = sum(x for _, x, _ in items) / len(items)
        balance_penalty = abs(avg_x - 4.5) / 4.5 * 28

    stability = clamp(stability - balance_penalty, 0, 100)

    disconnected_engines = 0
    for _part, ex, ey, _ok in engines:
        min_dist = min(
            (abs(ex - fx) + abs(ey - fy) for _fp, fx, fy in fuel_tanks),
            default=None,
        )
        connected = min_dist is not None and min_dist <= ENGINE_MAX_DIST
        if not connected:
            disconnected_engines += 1
    if engines and disconnected_engines:
        engine_power *= 1 - 0.3 * (disconnected_engines / len(engines))

    unsupported = 0
    for _part, hx, hy, _ok in heavy_parts:
        supported = any(
            sy == 4 and (abs(hx - sx) + abs(hy - sy)) <= SUPPORT_DIST
            for _sp, sx, sy in stabilizers
        )
        if not supported:
            unsupported += 1

    wrong_zone_count = sum(1 for ok in zone_ok.values() if not ok)

    buoyancy_score = clamp(buoyancy - weight / 22, 0, 100)
    structural_score = clamp(structural, 0, 100)
    engine_reliability = (
        clamp(48 + reliability + (8 if engine_count > 1 else 0), 0, 100)
        if engine_count > 0
        else 0
    )
    fuel_adequacy = clamp((fuel_capacity / max(weight * 0.55, 1)) * 100, 0, 100)
    range_est = (
        round((fuel_capacity / max(weight, 1)) * engine_power * 0.9)
        if engine_power > 0
        else 0
    )

    structural_stress = clamp(
        balance_penalty * 0.8
        + wrong_zone_count * 8
        + unsupported * 12
        + disconnected_engines * 10,
        0,
        100,
    )
    stability = clamp(stability - structural_stress * 0.12, 0, 100)

    return {
        "weight": round(weight),
        "stability": round(stability),
        "buoyancy": round(buoyancy_score),
        "structural": round(structural_score),
        "engine_power": round(engine_power),
        "fuel_capacity": round(fuel_capacity),
        "cargo_capacity": round(cargo_capacity),
        "range": range_est,
        "engine_reliability": round(engine_reliability),
        "fuel_adequacy": round(fuel_adequacy),
        "hull_count": hull_count,
        "engine_count": engine_count,
        "balance_penalty": round(balance_penalty),
        "wrong_zone_count": wrong_zone_count,
        "unsupported": unsupported,
        "disconnected_engines": disconnected_engines,
        "structural_stress": round(structural_stress),
    }


def run_inspection(stats):
    checks = [
        ("structural", "Structural Integrity", stats["structural"], stats["structural"] >= 45),
        ("stability", "Stability", stats["stability"], stats["stability"] >= 40),
        (
            "buoyancy",
            "Buoyancy",
            stats["buoyancy"],
            stats["buoyancy"] >= 40 and stats["hull_count"] > 0,
        ),
        (
            "engine",
            "Engine Reliability",
            stats["engine_reliability"],
            stats["engine_count"] > 0 and stats["engine_reliability"] >= 40,
        ),
        ("fuel", "Fuel Capacity", stats["fuel_adequacy"], stats["fuel_adequacy"] >= 35),
        (
            "balance",
            "Weight Balance",
            100 - stats["balance_penalty"],
            stats["balance_penalty"] <= 16,
        ),
        (
            "stress",
            "Structural Stress",
            100 - stats["structural_stress"],
            stats["structural_stress"] <= 45,
        ),
    ]
    overall = round(sum(v for _, _, v, _ in checks) / len(checks))
    approved = all(p for *_, p in checks) and overall >= 55

    issues = []
    if stats["hull_count"] == 0:
        issues.append("No hull part placed on the blueprint — the ship cannot float")
    if stats["engine_count"] == 0:
        issues.append("No engine placed — the ship cannot move")
    for key, label, val, passed in checks:
        if not passed and key not in ("buoyancy", "engine"):
            issues.append(f"{label} too low ({val}%)")
    if stats["wrong_zone_count"] > 0:
        issues.append(f"{stats['wrong_zone_count']} part(s) placed in the wrong zone")
    if stats["unsupported"] > 0:
        issues.append(f"{stats['unsupported']} heavy part(s) have no nearby stabilizer support")
    if stats["disconnected_engines"] > 0:
        issues.append(f"{stats['disconnected_engines']} engine(s) too far from any fuel tank")

    return overall, approved, issues
