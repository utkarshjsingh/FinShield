"""
FinShield - Revenue Simulation Engine

Generates monthly revenue trajectories for synthetic SMEs.

Revenue is influenced by:
    1. Base annual revenue
    2. Business growth trend
    3. Sector seasonality
    4. Subtype-specific seasonality
    5. Random monthly variation

Important:
This is synthetic financial simulation, not observed company data.
"""

import math
import random
from datetime import datetime

from config import (
    RANDOM_SEED,
    HISTORY_MONTHS,
    SECTOR_PROFILES,
)


# ============================================================
# RANDOM GENERATOR
# ============================================================

rng = random.Random(RANDOM_SEED + 100)


# ============================================================
# SEASONALITY PATTERNS
# ============================================================

# Month numbers:
# 1 = January
# ...
# 12 = December

BASE_SEASONALITY = {
    "retail": {
        1: 0.95,
        2: 0.92,
        3: 0.95,
        4: 0.98,
        5: 1.00,
        6: 0.98,
        7: 0.97,
        8: 1.00,
        9: 1.05,
        10: 1.18,   # festive period
        11: 1.15,
        12: 1.05,
    },

    "wholesale": {
        1: 0.97,
        2: 0.95,
        3: 1.00,
        4: 0.98,
        5: 1.00,
        6: 1.02,
        7: 1.00,
        8: 1.02,
        9: 1.05,
        10: 1.12,
        11: 1.08,
        12: 1.05,
    },

    "manufacturing": {
        1: 0.98,
        2: 0.97,
        3: 1.02,
        4: 0.98,
        5: 1.00,
        6: 1.02,
        7: 1.00,
        8: 1.02,
        9: 1.03,
        10: 1.05,
        11: 1.04,
        12: 1.00,
    },

    "food_hospitality": {
        1: 1.02,
        2: 1.00,
        3: 1.02,
        4: 1.05,
        5: 1.08,
        6: 1.00,
        7: 0.98,
        8: 1.00,
        9: 1.03,
        10: 1.10,
        11: 1.12,
        12: 1.18,
    },

    "professional_services": {
        1: 0.98,
        2: 0.98,
        3: 1.00,
        4: 1.00,
        5: 1.02,
        6: 1.02,
        7: 0.98,
        8: 1.00,
        9: 1.02,
        10: 1.03,
        11: 1.04,
        12: 1.05,
    },
}


# ============================================================
# SUBTYPE MODIFIERS
# ============================================================

SUBTYPE_SEASONALITY = {

    "grocery_fmcg": 1.02,
    "apparel": 1.08,
    "electronics": 1.06,
    "general_retail": 1.03,

    "fmcg_distribution": 1.02,
    "electronics_distribution": 1.06,
    "apparel_distribution": 1.07,
    "industrial_supplies": 1.00,

    "food_processing": 1.04,
    "textiles": 1.06,
    "auto_components": 1.02,
    "consumer_products": 1.05,
    "industrial_products": 1.00,

    "restaurant": 1.06,
    "cafe": 1.04,
    "catering": 1.10,
    "hotel": 1.12,
    "cloud_kitchen": 1.05,

    "it_services": 1.02,
    "consulting": 1.03,
    "marketing": 1.05,
    "accounting": 1.04,
    "legal_business_services": 1.02,
}


# ============================================================
# GROWTH RATES
# ============================================================

SECTOR_GROWTH_RANGES = {

    "retail": (0.04, 0.12),

    "wholesale": (0.04, 0.12),

    "manufacturing": (0.03, 0.10),

    "food_hospitality": (0.04, 0.12),

    "professional_services": (0.05, 0.15),
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_month_number(month_index):
    """
    Convert simulation month index into calendar month.

    Example:
        month_index = 0 → January
        month_index = 1 → February
        ...
        month_index = 11 → December
        month_index = 12 → January
    """

    return (month_index % 12) + 1


def get_date(month_index, start_date="2023-01-01"):
    """Return the calendar date for a simulation month."""

    start = datetime.strptime(
        start_date,
        "%Y-%m-%d"
    )

    year = (
        start.year
        + (start.month - 1 + month_index) // 12
    )

    month = (
        (start.month - 1 + month_index) % 12
    ) + 1

    return f"{year:04d}-{month:02d}-01"


def generate_growth_rate(sector):
    """Generate company-specific annual growth rate."""

    low, high = SECTOR_GROWTH_RANGES[sector]

    return rng.uniform(low, high)


def calculate_trend(annual_growth_rate, month_index):
    """
    Convert annual growth into a monthly compounded trend.
    """

    monthly_growth = (
        (1 + annual_growth_rate) ** (1 / 12)
    ) - 1

    return (1 + monthly_growth) ** month_index


def calculate_seasonality(
    sector,
    subtype,
    month_number
):
    """Calculate sector + subtype seasonal effect."""

    sector_pattern = BASE_SEASONALITY[sector]

    base_factor = sector_pattern[month_number]

    subtype_modifier = SUBTYPE_SEASONALITY.get(
        subtype,
        1.0
    )

    # Keep subtype effect modest.
    subtype_effect = (
        1 + (subtype_modifier - 1)
        * (base_factor - 1)
    )

    return base_factor * subtype_effect


def generate_noise():
    """
    Generate realistic month-to-month variation.

    The noise is centered around approximately 1.0,
    so it creates variation without systematically
    inflating revenue.
    """

    sigma = 0.04
    mu = -(sigma ** 2) / 2

    return rng.lognormvariate(
        mu,
        sigma
    )


# ============================================================
# MONTHLY REVENUE
# ============================================================

def generate_monthly_revenue(
    company,
    month_index,
    annual_growth_rate=None,
    shock_multiplier=1.0,
):
    """
    Generate revenue for one company-month.

    Parameters
    ----------
    company : dict
        Static company profile.

    month_index : int
        0-based simulation month.

    annual_growth_rate : float, optional
        Company-specific annual growth rate.

    shock_multiplier : float
        Future input from shock engine.
        Currently defaults to 1.0.
    """

    sector = company["sector"]
    subtype = company["subtype"]

    annual_revenue = company["annual_revenue"]

    base_monthly_revenue = (
        annual_revenue / 12
    )

    if annual_growth_rate is None:
        annual_growth_rate = generate_growth_rate(
            sector
        )

    trend = calculate_trend(
        annual_growth_rate,
        month_index
    )

    month_number = get_month_number(
        month_index
    )

    seasonality = calculate_seasonality(
        sector,
        subtype,
        month_number
    )

    noise = generate_noise()

    revenue = (
        base_monthly_revenue
        * trend
        * seasonality
        * noise
        * shock_multiplier
    )

    return round(max(revenue, 0), 2)


# ============================================================
# COMPLETE REVENUE TRAJECTORY
# ============================================================

def generate_revenue_trajectory(
    company,
    months=HISTORY_MONTHS,
    start_date="2023-01-01",
):
    """
    Generate a complete monthly revenue trajectory.

    Returns a list of dictionaries.
    """

    annual_growth_rate = generate_growth_rate(
        company["sector"]
    )

    trajectory = []

    for month_index in range(months):

        revenue = generate_monthly_revenue(
            company=company,
            month_index=month_index,
            annual_growth_rate=annual_growth_rate,
            shock_multiplier=1.0,
        )

        trajectory.append(
            {
                "company_id": company["company_id"],
                "month_index": month_index,
                "month": get_date(
                    month_index,
                    start_date
                ),
                "revenue": revenue,
                "annual_growth_rate": round(
                    annual_growth_rate,
                    4
                ),
                "seasonality": round(
                    calculate_seasonality(
                        company["sector"],
                        company["subtype"],
                        get_month_number(month_index),
                    ),
                    4
                ),
            }
        )

    return trajectory


# ============================================================
# SUMMARY
# ============================================================

def print_revenue_summary(trajectory):

    revenues = [
        row["revenue"]
        for row in trajectory
    ]

    total_revenue = sum(revenues)

    average_revenue = (
        total_revenue / len(revenues)
    )

    minimum_revenue = min(revenues)
    maximum_revenue = max(revenues)

    print("\n" + "=" * 60)
    print("FINSHIELD REVENUE ENGINE")
    print("=" * 60)

    print(
        f"Months simulated: {len(trajectory)}"
    )

    print(
        f"Total simulated revenue: "
        f"₹{total_revenue:,.2f}"
    )

    print(
        f"Average monthly revenue: "
        f"₹{average_revenue:,.2f}"
    )

    print(
        f"Minimum monthly revenue: "
        f"₹{minimum_revenue:,.2f}"
    )

    print(
        f"Maximum monthly revenue: "
        f"₹{maximum_revenue:,.2f}"
    )

    print("\nFirst 6 months:")

    for row in trajectory[:6]:

        print(
            f"  {row['month']} | "
            f"Revenue ₹{row['revenue']:,.0f} | "
            f"Seasonality {row['seasonality']}"
        )

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # Import the company generator only for testing.
    from company_generator import generate_companies

    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    trajectory = generate_revenue_trajectory(
        company=company,
        months=HISTORY_MONTHS,
    )

    print(
        f"\nTesting company: "
        f"{company['company_id']}"
    )

    print(
        f"Sector: {company['sector']}"
    )

    print(
        f"Subtype: {company['subtype']}"
    )

    print(
        f"Annual base revenue: "
        f"₹{company['annual_revenue']:,.0f}"
    )

    print_revenue_summary(
        trajectory
    )