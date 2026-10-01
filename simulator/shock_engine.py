"""
FinShield - Financial Shock Engine

Generates reproducible, sector-aware monthly shocks for the synthetic
SME simulator. Shocks are simulation assumptions, not observed events.

Output per month includes multipliers for:
    - revenue
    - DSO / collections
    - inventory target
    - COGS margin
    - DPO / supplier payment timing
    - operating expenses
"""

import random

from config import RANDOM_SEED, SHOCK_SEVERITY


SECTOR_SHOCK_WEIGHTS = {
    "retail": {
        "revenue_shock": 0.24,
        "dso_deterioration": 0.10,
        "inventory_buildup": 0.20,
        "cogs_shock": 0.18,
        "supplier_terms": 0.10,
        "expense_shock": 0.10,
        "multi_shock": 0.08,
    },
    "wholesale": {
        "revenue_shock": 0.14,
        "dso_deterioration": 0.22,
        "inventory_buildup": 0.16,
        "cogs_shock": 0.12,
        "supplier_terms": 0.16,
        "expense_shock": 0.06,
        "multi_shock": 0.14,
    },
    "manufacturing": {
        "revenue_shock": 0.12,
        "dso_deterioration": 0.16,
        "inventory_buildup": 0.14,
        "cogs_shock": 0.22,
        "supplier_terms": 0.16,
        "expense_shock": 0.05,
        "multi_shock": 0.15,
    },
    "food_hospitality": {
        "revenue_shock": 0.24,
        "dso_deterioration": 0.05,
        "inventory_buildup": 0.12,
        "cogs_shock": 0.22,
        "supplier_terms": 0.07,
        "expense_shock": 0.18,
        "multi_shock": 0.12,
    },
    "professional_services": {
        "revenue_shock": 0.14,
        "dso_deterioration": 0.25,
        "inventory_buildup": 0.01,
        "cogs_shock": 0.03,
        "supplier_terms": 0.04,
        "expense_shock": 0.24,
        "multi_shock": 0.29,
    },
}

# Probability that a company experiences at least one shock window in 36 months.
COMPANY_SHOCK_PROBABILITY = 0.72

SEVERITY_WEIGHTS = {
    "mild": 0.55,
    "moderate": 0.35,
    "severe": 0.10,
}

DURATION_BY_SEVERITY = {
    "mild": (1, 2),
    "moderate": (2, 4),
    "severe": (3, 6),
}


def _company_rng(company):
    """Stable RNG per company; avoids Python's randomized hash()."""
    company_id = str(company["company_id"])
    stable_number = sum((i + 1) * ord(ch) for i, ch in enumerate(company_id))
    return random.Random(RANDOM_SEED + 10_000 + stable_number)


def _weighted_choice(rng, weights):
    labels = list(weights.keys())
    values = list(weights.values())
    return rng.choices(labels, weights=values, k=1)[0]


def _empty_shock(month_index):
    return {
        "month_index": month_index,
        "active": False,
        "shock_type": "none",
        "severity": "none",
        "revenue_multiplier": 1.0,
        "dso_multiplier": 1.0,
        "inventory_multiplier": 1.0,
        "cogs_multiplier": 1.0,
        "dpo_multiplier": 1.0,
        "expense_multiplier": 1.0,
    }


def _build_event(rng, shock_type, severity, start_month, duration):
    severity_cfg = SHOCK_SEVERITY[severity]
    event = {
        "shock_type": shock_type,
        "severity": severity,
        "start_month": start_month,
        "end_month": start_month + duration - 1,
    }

    # Draw the magnitude once per event, then keep it stable through the event.
    revenue_change = rng.uniform(*severity_cfg["revenue_change"])
    dso_increase = rng.uniform(*severity_cfg["dso_increase"])
    inventory_increase = rng.uniform(*severity_cfg["inventory_days_increase"])
    cogs_increase = rng.uniform(*severity_cfg["cogs_increase"])

    event.update({
        "revenue_change": revenue_change,
        "dso_increase": dso_increase,
        "inventory_increase": inventory_increase,
        "cogs_increase": cogs_increase,
    })
    return event


def generate_shock_schedule(company, months):
    """Return one shock-state dictionary for every simulation month."""
    rng = _company_rng(company)
    schedule = [_empty_shock(i) for i in range(months)]

    if rng.random() > COMPANY_SHOCK_PROBABILITY or months < 6:
        return schedule

    sector = company["sector"]
    weights = SECTOR_SHOCK_WEIGHTS[sector]

    # Most companies get one event; a minority get a second overlapping event.
    event_count = 1 + (1 if rng.random() < 0.18 else 0)

    occupied = []
    for _ in range(event_count):
        shock_type = _weighted_choice(rng, weights)
        severity = _weighted_choice(rng, SEVERITY_WEIGHTS)
        min_duration, max_duration = DURATION_BY_SEVERITY[severity]
        duration = rng.randint(min_duration, max_duration)
        start_month = rng.randint(3, max(3, months - duration - 1))

        # Avoid excessive overlap unless the event is explicitly multi-shock.
        if shock_type != "multi_shock":
            attempts = 0
            while any(abs(start_month - s) < 2 for s, _ in occupied) and attempts < 10:
                start_month = rng.randint(3, max(3, months - duration - 1))
                attempts += 1

        event = _build_event(rng, shock_type, severity, start_month, duration)
        occupied.append((start_month, duration))

        for month_index in range(start_month, min(months, start_month + duration)):
            state = schedule[month_index]
            state["active"] = True
            state["shock_type"] = shock_type if state["shock_type"] == "none" else "multi_shock"
            state["severity"] = severity

            if shock_type in {"revenue_shock", "multi_shock"}:
                state["revenue_multiplier"] *= max(0.50, 1.0 + event["revenue_change"])

            if shock_type in {"dso_deterioration", "multi_shock"}:
                state["dso_multiplier"] *= 1.0 + event["dso_increase"] / 100.0

            if shock_type in {"inventory_buildup", "multi_shock"}:
                state["inventory_multiplier"] *= 1.0 + event["inventory_increase"] / 100.0

            if shock_type in {"cogs_shock", "multi_shock"}:
                state["cogs_multiplier"] *= 1.0 + event["cogs_increase"]

            if shock_type in {"supplier_terms", "multi_shock"}:
                # Tighter supplier terms => faster payment => lower DPO.
                state["dpo_multiplier"] *= max(0.45, 1.0 - event["dso_increase"] / 150.0)

            if shock_type in {"expense_shock", "multi_shock"}:
                state["expense_multiplier"] *= 1.0 + event["cogs_increase"] * 0.75

    return schedule


if __name__ == "__main__":
    sample = {
        "company_id": "C00001",
        "sector": "wholesale",
    }
    for row in generate_shock_schedule(sample, 36):
        if row["active"]:
            print(row)
