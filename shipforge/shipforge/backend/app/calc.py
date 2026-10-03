def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compute_stats(items, material):
    """items: list of (Part, x, y) tuples. material: Material row."""
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

    for part, _x, _y in items:
        w = part.base_weight * material.weight_mult
        weight += w
        if part.buoyancy:
            buoyancy += part.buoyancy
            hull_count += 1
        if part.structural:
            structural += part.structural * material.strength_mult
        if part.stability:
            stability += part.stability
        if part.engine_power:
            engine_power += part.engine_power
            engine_count += 1
        if part.fuel_capacity:
            fuel_capacity += part.fuel_capacity
        if part.cargo_capacity:
            cargo_capacity += part.cargo_capacity
        if part.safety:
            safety += part.safety
        if part.reliability:
            reliability += part.reliability

    balance_penalty = 0.0
    if items:
        avg_x = sum(x for _, x, _ in items) / len(items)
        dev = abs(avg_x - 4.5) / 4.5
        balance_penalty = dev * 28

    stability = clamp(stability - balance_penalty, 0, 100)
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

    return {
        "weight": round(weight),
        "stability": round(stability),
        "buoyancy": round(buoyancy_score),
        "structural": round(structural_score),
        "engine_power": engine_power,
        "fuel_capacity": fuel_capacity,
        "cargo_capacity": cargo_capacity,
        "range": range_est,
        "engine_reliability": round(engine_reliability),
        "fuel_adequacy": round(fuel_adequacy),
        "safety_equip": round(clamp(safety, 0, 100)),
        "hull_count": hull_count,
        "engine_count": engine_count,
        "balance_penalty": round(balance_penalty),
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

    return overall, approved, issues
