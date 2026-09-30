"""
FinShield - Synthetic SME Company Generator

Generates static characteristics for synthetic Indian SMEs.

This module does NOT simulate monthly financials.
It only creates the initial company-level characteristics
that will later feed the monthly financial simulation engine.
"""

import csv
import random
from pathlib import Path

from config import (
    RANDOM_SEED,
    SIZE_PROFILES,
    SECTOR_PROFILES,
    PROTOTYPE_COMPANIES,
)


# ============================================================
# RANDOM NUMBER GENERATOR
# ============================================================

rng = random.Random(RANDOM_SEED)


# ============================================================
# CONSTANTS
# ============================================================

SECTORS = list(SECTOR_PROFILES.keys())

SIZES = ["micro", "small", "medium"]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clipped_uniform(low, high):
    """Generate a random value between low and high."""
    return rng.uniform(low, high)


def generate_revenue(size):
    """
    Generate annual revenue.

    Log-uniform sampling is used instead of uniform sampling
    because business sizes tend to span large ranges.
    """

    profile = SIZE_PROFILES[size]

    low = profile["annual_revenue_min"]
    high = profile["annual_revenue_max"]

    log_value = rng.uniform(
        __import__("math").log(low),
        __import__("math").log(high)
    )

    return round(__import__("math").exp(log_value), 2)


def generate_employees(size, annual_revenue):
    """
    Generate employee count.

    Revenue and employee count are positively related,
    but not perfectly correlated.
    """

    profile = SIZE_PROFILES[size]

    min_emp = profile["employees_min"]
    max_emp = profile["employees_max"]

    # Approximate revenue position within the size band
    revenue_min = profile["annual_revenue_min"]
    revenue_max = profile["annual_revenue_max"]

    revenue_position = (
        (annual_revenue - revenue_min)
        / (revenue_max - revenue_min)
    )

    revenue_position = max(0.0, min(1.0, revenue_position))

    expected_employees = (
        min_emp
        + revenue_position * (max_emp - min_emp)
    )

    # Add business-level variation
    variation = rng.uniform(0.75, 1.25)

    employees = int(expected_employees * variation)

    return max(min_emp, min(max_emp, employees))


def generate_starting_cash(size, annual_revenue):
    """Generate initial cash based on operating expense needs."""

    profile = SIZE_PROFILES[size]

    cash_months = clipped_uniform(
        profile["starting_cash_months_min"],
        profile["starting_cash_months_max"]
    )

    # Approximate monthly operating scale
    monthly_revenue = annual_revenue / 12

    # Starting cash is a fraction of monthly operating scale.
    # This will later be refined by the expense engine.
    starting_cash = monthly_revenue * cash_months * 0.45

    return round(starting_cash, 2)


def generate_debt(size, annual_revenue):
    """Generate initial debt balance."""

    profile = SIZE_PROFILES[size]

    debt_ratio = clipped_uniform(
        profile["debt_intensity"][0],
        profile["debt_intensity"][1]
    )

    debt = annual_revenue * debt_ratio

    # Debt should not become unrealistically large.
    debt = min(debt, annual_revenue * 0.80)

    return round(debt, 2)


def generate_credit_limit(size, annual_revenue):
    """Generate working-capital credit facility."""

    profile = SIZE_PROFILES[size]

    utilization = clipped_uniform(
        profile["credit_utilization"][0],
        profile["credit_utilization"][1]
    )

    # Credit limit is related to business scale.
    credit_limit = annual_revenue * rng.uniform(
        0.05,
        0.25
    )

    # Current outstanding balance
    credit_balance = credit_limit * utilization

    return round(credit_limit, 2), round(credit_balance, 2)


def generate_customer_concentration(sector):
    """
    Generate percentage of revenue coming from the
    largest customer.

    Higher concentration creates greater liquidity risk.
    """

    if sector == "wholesale":
        low, high = 0.10, 0.45

    elif sector == "manufacturing":
        low, high = 0.10, 0.50

    elif sector == "professional_services":
        low, high = 0.10, 0.55

    elif sector == "retail":
        low, high = 0.03, 0.20

    else:  # food & hospitality
        low, high = 0.03, 0.25

    return round(clipped_uniform(low, high), 3)


def generate_location_factor():
    """
    Represents differences in operating environment,
    rent, wages, demand, etc.

    This is NOT geographic identification.
    It is simply a simulation parameter.
    """

    return round(rng.uniform(0.85, 1.20), 3)


def generate_company(company_id, sector, size):
    """Generate one complete synthetic company."""

    sector_config = SECTOR_PROFILES[sector]

    subtype = rng.choice(
        sector_config["subtypes"]
    )

    annual_revenue = generate_revenue(size)

    employees = generate_employees(
        size,
        annual_revenue
    )

    starting_cash = generate_starting_cash(
        size,
        annual_revenue
    )

    debt_balance = generate_debt(
        size,
        annual_revenue
    )

    credit_limit, credit_balance = generate_credit_limit(
        size,
        annual_revenue
    )

    customer_concentration = generate_customer_concentration(
        sector
    )

    location_factor = generate_location_factor()

    return {
        "company_id": company_id,
        "sector": sector,
        "company_size": size,
        "subtype": subtype,

        "annual_revenue": annual_revenue,
        "employees": employees,

        "starting_cash": starting_cash,

        "debt_balance": debt_balance,

        "credit_limit": credit_limit,
        "credit_balance": credit_balance,

        "customer_concentration": customer_concentration,

        "location_factor": location_factor,
    }


# ============================================================
# COMPANY DISTRIBUTION
# ============================================================

def create_sector_size_plan(total_companies):
    """
    Create approximately equal representation across sectors
    and sizes.

    For the 50-company prototype:

        10 Retail
        10 Wholesale
        10 Manufacturing
        10 Food & Hospitality
        10 Professional Services

    Within each sector, Micro/Small/Medium are approximately
    balanced.
    """

    base_per_sector = total_companies // len(SECTORS)
    remainder = total_companies % len(SECTORS)

    plan = []

    company_number = 1

    for sector_index, sector in enumerate(SECTORS):

        sector_count = base_per_sector

        if sector_index < remainder:
            sector_count += 1

        # Rotate sizes so representation remains balanced
        for i in range(sector_count):

            size = SIZES[
                (i + sector_index) % len(SIZES)
            ]

            plan.append(
                {
                    "company_number": company_number,
                    "sector": sector,
                    "size": size,
                }
            )

            company_number += 1

    return plan


# ============================================================
# GENERATE COMPANIES
# ============================================================

def generate_companies(total_companies=PROTOTYPE_COMPANIES):

    plan = create_sector_size_plan(
        total_companies
    )

    companies = []

    for item in plan:

        company_id = (
            f"SME_{item['company_number']:06d}"
        )

        company = generate_company(
            company_id=company_id,
            sector=item["sector"],
            size=item["size"],
        )

        companies.append(company)

    return companies


# ============================================================
# SAVE DATA
# ============================================================

def save_companies(companies):

    output_directory = Path("data/raw")

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_directory / "companies.csv"
    )

    fieldnames = list(
        companies[0].keys()
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(companies)

    return output_file


# ============================================================
# SUMMARY
# ============================================================

def print_summary(companies):

    print("\n" + "=" * 60)
    print("FINSHIELD COMPANY GENERATOR")
    print("=" * 60)

    print(
        f"Companies generated: {len(companies)}"
    )

    print("\nSector distribution:")

    sector_counts = {}

    for company in companies:

        sector = company["sector"]

        sector_counts[sector] = (
            sector_counts.get(sector, 0) + 1
        )

    for sector, count in sector_counts.items():

        print(
            f"  {sector:<25} {count}"
        )

    print("\nSize distribution:")

    size_counts = {}

    for company in companies:

        size = company["company_size"]

        size_counts[size] = (
            size_counts.get(size, 0) + 1
        )

    for size, count in size_counts.items():

        print(
            f"  {size:<25} {count}"
        )

    print("\nFirst 5 companies:")

    for company in companies[:5]:

        print(
            f"  {company['company_id']} | "
            f"{company['sector']} | "
            f"{company['company_size']} | "
            f"₹{company['annual_revenue']:,.0f}"
        )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    companies = generate_companies()

    output_file = save_companies(
        companies
    )

    print_summary(companies)

    print(
        f"\nSaved to: {output_file}"
    )