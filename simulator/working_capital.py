"""
FinShield - Working Capital Simulation Engine

Simulates:
    - Cash sales
    - Credit sales
    - Accounts Receivable (AR)
    - Customer collections
    - COGS
    - Inventory
    - Purchases
    - Accounts Payable (AP)
    - Supplier payments

This module connects revenue to working-capital balances.
"""

import math
import random

from config import RANDOM_SEED


# ============================================================
# RANDOM GENERATOR
# ============================================================

rng = random.Random(RANDOM_SEED + 200)


# ============================================================
# GENERAL HELPERS
# ============================================================

def uniform(low, high):
    """Generate a random value between low and high."""
    return rng.uniform(low, high)


def clamp(value, low, high):
    """Keep value within a specified range."""
    return max(low, min(high, value))


# ============================================================
# COMPANY-LEVEL WORKING CAPITAL PARAMETERS
# ============================================================

def generate_working_capital_parameters(company):
    """
    Generate company-specific working-capital parameters.

    These remain fixed for the company unless the future
    shock engine changes them.
    """

    sector = company["sector"]
    size = company["company_size"]

    # Import here to keep configuration centralized.
    from config import SECTOR_PROFILES

    sector_config = SECTOR_PROFILES[sector]

    cash_sales_low, cash_sales_high = (
        sector_config["cash_sales_pct"][size]
    )

    dso_low, dso_high = (
        sector_config["dso_days"][size]
    )

    inventory_low, inventory_high = (
        sector_config["inventory_days"][size]
    )

    dpo_low, dpo_high = (
        sector_config["dpo_days"][size]
    )

    cogs_low, cogs_high = (
        sector_config["cogs_margin"]
    )

    return {
        "cash_sales_pct": uniform(
            cash_sales_low,
            cash_sales_high,
        ),

        "dso_days": uniform(
            dso_low,
            dso_high,
        ),

        "inventory_days": uniform(
            inventory_low,
            inventory_high,
        ),

        "dpo_days": uniform(
            dpo_low,
            dpo_high,
        ),

        "cogs_margin": uniform(
            cogs_low,
            cogs_high,
        ),

        # Most wholesale/manufacturing purchases
        # are assumed to involve supplier credit.
        "credit_purchase_pct": uniform(
            0.65,
            0.95,
        ),
    }


# ============================================================
# PAYMENT PROFILE
# ============================================================

def create_payment_profile(
    average_days,
    max_months=7,
):
    """
    Convert an average payment period into a monthly
    payment distribution.

    Example:

        DSO = 45 days

    A credit invoice will not necessarily be paid
    exactly after 45 days.

    Instead, payments are distributed across monthly
    cohorts, creating realistic variation.

    Returns:
        {
            month_lag: payment_fraction
        }
    """

    # Prevent unrealistic values.
    average_days = clamp(
        average_days,
        1,
        180,
    )

    # Gamma distribution parameters.
    # Shape > 1 creates a concentration around the mean
    # rather than an extremely long-tailed distribution.
    shape = 4.0

    scale = average_days / shape

    weights = []

    for month_lag in range(max_months):

        lower_day = month_lag * 30
        upper_day = (month_lag + 1) * 30

        # Approximate probability mass in this interval.
        midpoint = (
            lower_day + upper_day
        ) / 2

        if midpoint <= 0:
            midpoint = 1

        weight = (
            midpoint ** (shape - 1)
            * math.exp(-midpoint / scale)
        )

        weights.append(max(weight, 0))

    total_weight = sum(weights)

    if total_weight == 0:
        return {
            0: 1.0
        }

    profile = {}

    for lag, weight in enumerate(weights):

        profile[lag] = (
            weight / total_weight
        )

    return profile


# ============================================================
# CREDIT SALES / AR
# ============================================================

def calculate_sales_components(
    revenue,
    cash_sales_pct,
):
    """
    Split revenue into cash and credit sales.
    """

    cash_sales = (
        revenue * cash_sales_pct
    )

    credit_sales = (
        revenue - cash_sales
    )

    return (
        cash_sales,
        credit_sales,
    )


# ============================================================
# CUSTOMER COLLECTIONS
# ============================================================

def calculate_collections(
    credit_sales_history,
    current_month,
    payment_profile,
):
    """
    Calculate customer collections for the current month.

    Previous credit-sales cohorts contribute to current
    collections according to their payment profile.
    """

    collections = 0.0

    for lag, payment_fraction in payment_profile.items():

        source_month = (
            current_month - lag
        )

        if source_month < 0:
            continue

        if source_month >= len(
            credit_sales_history
        ):
            continue

        collections += (
            credit_sales_history[source_month]
            * payment_fraction
        )

    return collections


# ============================================================
# COGS
# ============================================================

def calculate_cogs(
    revenue,
    cogs_margin,
):
    """Calculate monthly cost of goods sold."""

    return revenue * cogs_margin


# ============================================================
# INVENTORY
# ============================================================

def calculate_target_inventory(
    cogs,
    inventory_days,
):
    """
    Estimate inventory required for the desired
    inventory holding period.
    """

    return (
        cogs
        * inventory_days
        / 30
    )


def calculate_purchases(
    cogs,
    beginning_inventory,
    target_inventory,
):
    """
    Calculate purchases required to satisfy COGS and
    maintain the desired inventory level.
    """

    required_purchases = (
        cogs
        + target_inventory
        - beginning_inventory
    )

    return max(
        required_purchases,
        0.0,
    )


# ============================================================
# SUPPLIER PAYMENTS / AP
# ============================================================

def calculate_supplier_payments(
    credit_purchase_history,
    current_month,
    supplier_payment_profile,
):
    """
    Calculate supplier payments from previous
    credit-purchase cohorts.
    """

    payments = 0.0

    for lag, payment_fraction in (
        supplier_payment_profile.items()
    ):

        source_month = (
            current_month - lag
        )

        if source_month < 0:
            continue

        if source_month >= len(
            credit_purchase_history
        ):
            continue

        payments += (
            credit_purchase_history[source_month]
            * payment_fraction
        )

    return payments


# ============================================================
# MAIN WORKING CAPITAL ENGINE
# ============================================================

def simulate_working_capital(
    company,
    revenue_trajectory,
):
    """
    Simulate working capital across the complete
    revenue trajectory.

    Parameters
    ----------
    company : dict
        Static company profile.

    revenue_trajectory : list
        Output from revenue_engine.generate_revenue_trajectory()

    Returns
    -------
    list of dict
        Monthly working-capital records.
    """

    parameters = (
        generate_working_capital_parameters(
            company
        )
    )

    cash_sales_pct = parameters[
        "cash_sales_pct"
    ]

    dso_days = parameters[
        "dso_days"
    ]

    inventory_days = parameters[
        "inventory_days"
    ]

    dpo_days = parameters[
        "dpo_days"
    ]

    cogs_margin = parameters[
        "cogs_margin"
    ]

    credit_purchase_pct = parameters[
        "credit_purchase_pct"
    ]

    # Customer payment behaviour
    customer_payment_profile = (
        create_payment_profile(
            dso_days
        )
    )

    # Supplier payment behaviour
    supplier_payment_profile = (
        create_payment_profile(
            dpo_days
        )
    )

    credit_sales_history = []
    credit_purchase_history = []

    results = []

    # Initial balances.
    accounts_receivable = 0.0
    inventory = 0.0
    accounts_payable = 0.0

    for month_index, row in enumerate(
        revenue_trajectory
    ):

        revenue = row["revenue"]

        # ----------------------------------------------------
        # SALES
        # ----------------------------------------------------

        cash_sales, credit_sales = (
            calculate_sales_components(
                revenue,
                cash_sales_pct,
            )
        )

        credit_sales_history.append(
            credit_sales
        )

        # ----------------------------------------------------
        # CUSTOMER COLLECTIONS
        # ----------------------------------------------------

        collections = (
            calculate_collections(
                credit_sales_history,
                month_index,
                customer_payment_profile,
            )
        )

        # ----------------------------------------------------
        # AR
        # ----------------------------------------------------

        beginning_ar = (
            accounts_receivable
        )

        accounts_receivable = max(
            beginning_ar
            + credit_sales
            - collections,
            0.0,
        )

        # ----------------------------------------------------
        # COGS
        # ----------------------------------------------------

        cogs = calculate_cogs(
            revenue,
            cogs_margin,
        )

        # ----------------------------------------------------
        # INVENTORY
        # ----------------------------------------------------

        beginning_inventory = inventory

        target_inventory = (
            calculate_target_inventory(
                cogs,
                inventory_days,
            )
        )

        purchases = calculate_purchases(
            cogs,
            beginning_inventory,
            target_inventory,
        )

        inventory = max(
            beginning_inventory
            + purchases
            - cogs,
            0.0,
        )

        # ----------------------------------------------------
        # SUPPLIER CREDIT
        # ----------------------------------------------------

        credit_purchases = (
            purchases
            * credit_purchase_pct
        )

        cash_purchases = (
            purchases
            - credit_purchases
        )

        credit_purchase_history.append(
            credit_purchases
        )

        # ----------------------------------------------------
        # SUPPLIER PAYMENTS
        # ----------------------------------------------------

        supplier_payments = (
            calculate_supplier_payments(
                credit_purchase_history,
                month_index,
                supplier_payment_profile,
            )
        )

        # ----------------------------------------------------
        # AP
        # ----------------------------------------------------

        beginning_ap = (
            accounts_payable
        )

        accounts_payable = max(
            beginning_ap
            + credit_purchases
            - supplier_payments,
            0.0,
        )

        # ----------------------------------------------------
        # WORKING CAPITAL METRICS
        # ----------------------------------------------------

        if credit_sales > 0:

            dso_estimated = (
                accounts_receivable
                / credit_sales
                * 30
            )

        else:

            dso_estimated = 0.0

        if cogs > 0:

            inventory_days_estimated = (
                inventory
                / cogs
                * 30
            )

        else:

            inventory_days_estimated = 0.0

        if credit_purchases > 0:

            dpo_estimated = (
                accounts_payable
                / credit_purchases
                * 30
            )

        else:

            dpo_estimated = 0.0

        cash_conversion_cycle = (
            dso_estimated
            + inventory_days_estimated
            - dpo_estimated
        )

        # ----------------------------------------------------
        # SAVE MONTH
        # ----------------------------------------------------

        results.append(
            {
                "company_id": company[
                    "company_id"
                ],

                "month_index": row[
                    "month_index"
                ],

                "month": row[
                    "month"
                ],

                "revenue": revenue,

                "cash_sales": cash_sales,
                "credit_sales": credit_sales,
                "collections": collections,

                "accounts_receivable":
                    accounts_receivable,

                "cogs": cogs,

                "beginning_inventory":
                    beginning_inventory,

                "purchases": purchases,

                "cash_purchases":
                    cash_purchases,

                "credit_purchases":
                    credit_purchases,

                "inventory": inventory,

                "supplier_payments":
                    supplier_payments,

                "accounts_payable":
                    accounts_payable,

                "dso": dso_estimated,

                "inventory_days":
                    inventory_days_estimated,

                "dpo": dpo_estimated,

                "cash_conversion_cycle":
                    cash_conversion_cycle,

                # Company-level parameters
                "cash_sales_pct":
                    cash_sales_pct,

                "cogs_margin":
                    cogs_margin,

                "target_inventory_days":
                    inventory_days,

                "target_dso":
                    dso_days,

                "target_dpo":
                    dpo_days,
            }
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_working_capital_summary(
    results
):
    """Print a simple diagnostic summary."""

    latest = results[-1]

    print("\n" + "=" * 70)
    print("FINSHIELD WORKING CAPITAL ENGINE")
    print("=" * 70)

    print(
        f"Months simulated: "
        f"{len(results)}"
    )

    print(
        f"\nLatest month: "
        f"{latest['month']}"
    )

    print(
        f"Revenue: "
        f"₹{latest['revenue']:,.0f}"
    )

    print(
        f"Credit sales: "
        f"₹{latest['credit_sales']:,.0f}"
    )

    print(
        f"Collections: "
        f"₹{latest['collections']:,.0f}"
    )

    print(
        f"Accounts Receivable: "
        f"₹{latest['accounts_receivable']:,.0f}"
    )

    print(
        f"Inventory: "
        f"₹{latest['inventory']:,.0f}"
    )

    print(
        f"Accounts Payable: "
        f"₹{latest['accounts_payable']:,.0f}"
    )

    print(
        f"DSO: "
        f"{latest['dso']:.1f} days"
    )

    print(
        f"Inventory Days: "
        f"{latest['inventory_days']:.1f} days"
    )

    print(
        f"DPO: "
        f"{latest['dpo']:.1f} days"
    )

    print(
        f"Cash Conversion Cycle: "
        f"{latest['cash_conversion_cycle']:.1f} days"
    )

    print("=" * 70)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from company_generator import (
        generate_companies,
    )

    from revenue_engine import (
        generate_revenue_trajectory,
    )

    # Generate one company
    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    # Generate 36 months of revenue
    revenue_trajectory = (
        generate_revenue_trajectory(
            company=company,
            months=36,
        )
    )

    # Simulate working capital
    results = simulate_working_capital(
        company=company,
        revenue_trajectory=revenue_trajectory,
    )

    print(
        f"\nTesting company: "
        f"{company['company_id']}"
    )

    print(
        f"Sector: "
        f"{company['sector']}"
    )

    print(
        f"Subtype: "
        f"{company['subtype']}"
    )

    print_working_capital_summary(
        results
    )