"""
FinShield - Working Capital Simulation Engine

Simulates:
    - Cash sales
    - Credit sales
    - Accounts Receivable
    - Customer collections
    - COGS
    - Inventory
    - Purchases
    - Accounts Payable
    - Supplier payments

The simulation begins with realistic opening AR, inventory
and AP balances instead of assuming every company starts
with zero working capital.
"""

import math
import random

from config import RANDOM_SEED


rng = random.Random(RANDOM_SEED + 200)


# ============================================================
# HELPERS
# ============================================================

def uniform(low, high):
    return rng.uniform(low, high)


def clamp(value, low, high):
    return max(low, min(high, value))


# ============================================================
# COMPANY PARAMETERS
# ============================================================

def generate_working_capital_parameters(company):

    from config import SECTOR_PROFILES

    sector = company["sector"]
    size = company["company_size"]

    config = SECTOR_PROFILES[sector]

    cash_low, cash_high = config[
        "cash_sales_pct"
    ][size]

    dso_low, dso_high = config[
        "dso_days"
    ][size]

    inventory_low, inventory_high = config[
        "inventory_days"
    ][size]

    dpo_low, dpo_high = config[
        "dpo_days"
    ][size]

    cogs_low, cogs_high = config[
        "cogs_margin"
    ]

    return {
        "cash_sales_pct": uniform(
            cash_low,
            cash_high
        ),

        "dso_days": uniform(
            dso_low,
            dso_high
        ),

        "inventory_days": uniform(
            inventory_low,
            inventory_high
        ),

        "dpo_days": uniform(
            dpo_low,
            dpo_high
        ),

        "cogs_margin": uniform(
            cogs_low,
            cogs_high
        ),

        "credit_purchase_pct": uniform(
            0.65,
            0.90
        ),
    }


# ============================================================
# PAYMENT PROFILE
# ============================================================

def create_payment_profile(
    average_days,
    max_months=7
):
    """
    Creates a payment distribution around the target
    DSO/DPO instead of forcing every invoice to be paid
    on exactly one date.
    """

    average_days = clamp(
        average_days,
        1,
        180
    )

    shape = 4.0
    scale = average_days / shape

    weights = []

    for month_lag in range(max_months):

        lower_day = month_lag * 30
        upper_day = (month_lag + 1) * 30

        midpoint = (
            lower_day + upper_day
        ) / 2

        if midpoint <= 0:
            midpoint = 1

        weight = (
            midpoint ** (shape - 1)
            * math.exp(
                -midpoint / scale
            )
        )

        weights.append(
            max(weight, 0)
        )

    total = sum(weights)

    if total <= 0:
        return {0: 1.0}

    return {
        lag: weight / total
        for lag, weight in enumerate(weights)
    }


# ============================================================
# SALES
# ============================================================

def calculate_sales_components(
    revenue,
    cash_sales_pct
):

    cash_sales = (
        revenue
        * cash_sales_pct
    )

    credit_sales = (
        revenue
        - cash_sales
    )

    return (
        cash_sales,
        credit_sales
    )


# ============================================================
# COLLECTIONS
# ============================================================

def calculate_collections(
    credit_sales_history,
    current_month,
    payment_profile,
    opening_ar=0.0,
    opening_ar_collection_fraction=0.0
):
    """
    Collections consist of:

    1. Collections from simulated invoice cohorts.
    2. A portion of opening AR from before simulation began.
    """

    collections = 0.0

    # Opening AR collection.
    if current_month == 0:

        collections += (
            opening_ar
            * opening_ar_collection_fraction
        )

    # Historical simulated invoices.
    for lag, fraction in (
        payment_profile.items()
    ):

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
            credit_sales_history[
                source_month
            ]
            * fraction
        )

    return collections


# ============================================================
# COGS
# ============================================================

def calculate_cogs(
    revenue,
    cogs_margin
):

    return revenue * cogs_margin


# ============================================================
# INVENTORY
# ============================================================

def calculate_target_inventory(
    cogs,
    inventory_days
):

    return (
        cogs
        * inventory_days
        / 30
    )


def calculate_purchases(
    cogs,
    beginning_inventory,
    target_inventory
):

    purchases = (
        cogs
        + target_inventory
        - beginning_inventory
    )

    return max(
        purchases,
        0.0
    )


# ============================================================
# SUPPLIER PAYMENTS
# ============================================================

def calculate_supplier_payments(
    credit_purchase_history,
    current_month,
    payment_profile,
    opening_ap=0.0,
    opening_ap_payment_fraction=0.0
):
    """
    Supplier payments consist of:

    1. A portion of opening AP.
    2. Payments against simulated credit purchases.
    """

    payments = 0.0

    if current_month == 0:

        payments += (
            opening_ap
            * opening_ap_payment_fraction
        )

    for lag, fraction in (
        payment_profile.items()
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
            credit_purchase_history[
                source_month
            ]
            * fraction
        )

    return payments


# ============================================================
# MAIN ENGINE
# ============================================================

def simulate_working_capital(
    company,
    revenue_trajectory,
    shock_schedule=None,
):

    parameters = (
        generate_working_capital_parameters(
            company
        )
    )

    if shock_schedule is None:
        shock_schedule = [
            {"active": False}
            for _ in revenue_trajectory
        ]

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

    customer_payment_profile = (
        create_payment_profile(
            dso_days
        )
    )

    supplier_payment_profile = (
        create_payment_profile(
            dpo_days
        )
    )

    # --------------------------------------------------------
    # Opening working capital
    # --------------------------------------------------------

    first_revenue = revenue_trajectory[0][
        "revenue"
    ]

    first_cogs = calculate_cogs(
        first_revenue,
        cogs_margin
    )

    (
        first_cash_sales,
        first_credit_sales
    ) = calculate_sales_components(
        first_revenue,
        cash_sales_pct
    )

    opening_ar = (
        first_credit_sales
        * dso_days
        / 30
    )

    opening_inventory = (
        first_cogs
        * inventory_days
        / 30
    )

    opening_purchases = first_cogs

    opening_credit_purchases = (
        opening_purchases
        * credit_purchase_pct
    )

    opening_ap = (
        opening_credit_purchases
        * dpo_days
        / 30
    )

    # Opening balances are non-negative.
    opening_ar = max(
        opening_ar,
        0.0
    )

    opening_inventory = max(
        opening_inventory,
        0.0
    )

    opening_ap = max(
        opening_ap,
        0.0
    )

    # Fraction of opening balances collected/paid
    # during the first month.
    opening_ar_fraction = (
        customer_payment_profile.get(
            0,
            0.0
        )
    )

    opening_ap_fraction = (
        supplier_payment_profile.get(
            0,
            0.0
        )
    )

    # --------------------------------------------------------
    # Historical invoice / purchase cohorts
    # --------------------------------------------------------

    credit_sales_history = []

    credit_purchase_history = []

    # --------------------------------------------------------
    # Rolling histories for stable financial ratios
    # --------------------------------------------------------

    recent_ar = []
    recent_credit_sales = []

    recent_inventory = []
    recent_cogs = []

    recent_ap = []
    recent_credit_purchases = []

    # --------------------------------------------------------
    # Current balances
    # --------------------------------------------------------

    results = []

    accounts_receivable = opening_ar
    inventory = opening_inventory
    accounts_payable = opening_ap

    # ========================================================
    # MONTHLY SIMULATION
    # ========================================================

    for month_index, row in enumerate(
        revenue_trajectory
    ):

        revenue = row["revenue"]

        shock = shock_schedule[
            month_index
        ]

        # ----------------------------------------------------
        # Apply monthly shock parameters
        # ----------------------------------------------------

        month_dso_days = (
            dso_days
            * shock.get(
                "dso_multiplier",
                1.0
            )
        )

        month_inventory_days = (
            inventory_days
            * shock.get(
                "inventory_multiplier",
                1.0
            )
        )

        month_cogs_margin = clamp(
            cogs_margin
            * shock.get(
                "cogs_multiplier",
                1.0
            ),
            0.01,
            0.98,
        )

        month_dpo_days = (
            dpo_days
            * shock.get(
                "dpo_multiplier",
                1.0
            )
        )

        # Keep shock-adjusted target assumptions
        # financially bounded.
        month_dso_days = clamp(
            month_dso_days,
            1,
            180
        )

        month_inventory_days = clamp(
            month_inventory_days,
            1,
            180
        )

        month_dpo_days = clamp(
            month_dpo_days,
            1,
            180
        )

        # ----------------------------------------------------
        # Payment profiles
        # ----------------------------------------------------

        month_customer_payment_profile = (
            create_payment_profile(
                month_dso_days
            )
        )

        month_supplier_payment_profile = (
            create_payment_profile(
                month_dpo_days
            )
        )

        # ====================================================
        # SALES
        # ====================================================

        (
            cash_sales,
            credit_sales
        ) = calculate_sales_components(
            revenue,
            cash_sales_pct
        )

        credit_sales_history.append(
            credit_sales
        )

        # ====================================================
        # COLLECTIONS
        # ====================================================

        collections = calculate_collections(
            credit_sales_history,
            month_index,
            month_customer_payment_profile,
            opening_ar,
            opening_ar_fraction
        )

        # Collections cannot exceed available
        # opening/current AR.
        collections = min(
            collections,
            accounts_receivable
            + credit_sales
        )

        beginning_ar = accounts_receivable

        accounts_receivable = max(
            beginning_ar
            + credit_sales
            - collections,
            0.0
        )

        # ====================================================
        # COGS
        # ====================================================

        cogs = calculate_cogs(
            revenue,
            month_cogs_margin
        )

        # ====================================================
        # INVENTORY
        # ====================================================

        beginning_inventory = inventory

        target_inventory = (
            calculate_target_inventory(
                cogs,
                month_inventory_days
            )
        )

        purchases = calculate_purchases(
            cogs,
            beginning_inventory,
            target_inventory
        )

        inventory = max(
            beginning_inventory
            + purchases
            - cogs,
            0.0
        )

        # ====================================================
        # PURCHASES / ACCOUNTS PAYABLE
        # ====================================================

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

        supplier_payments = (
            calculate_supplier_payments(
                credit_purchase_history,
                month_index,
                month_supplier_payment_profile,
                opening_ap,
                opening_ap_fraction
            )
        )

        supplier_payments = min(
            supplier_payments,
            accounts_payable
            + credit_purchases
        )

        beginning_ap = accounts_payable

        accounts_payable = max(
            beginning_ap
            + credit_purchases
            - supplier_payments,
            0.0
        )

        # ====================================================
        # ROLLING HISTORIES
        # ====================================================

        recent_ar.append(
            accounts_receivable
        )

        recent_credit_sales.append(
            credit_sales
        )

        recent_inventory.append(
            inventory
        )

        recent_cogs.append(
            cogs
        )

        recent_ap.append(
            accounts_payable
        )

        recent_credit_purchases.append(
            credit_purchases
        )

        histories = [
            recent_ar,
            recent_credit_sales,
            recent_inventory,
            recent_cogs,
            recent_ap,
            recent_credit_purchases,
        ]

        for history in histories:

            if len(history) > 3:
                history.pop(0)

        # ====================================================
        # STABLE WORKING CAPITAL METRICS
        # ====================================================

        total_recent_credit_sales = (
            sum(recent_credit_sales)
        )

        total_recent_cogs = (
            sum(recent_cogs)
        )

        total_recent_credit_purchases = (
            sum(recent_credit_purchases)
        )

        # ----------------------------------------------------
        # DSO
        # ----------------------------------------------------
        #
        # If there is virtually no credit-sales activity,
        # DSO is not economically meaningful. We therefore
        # return 0 rather than allowing a tiny denominator
        # to create a huge artificial ratio.
        #

        if total_recent_credit_sales <= 0:

            dso_estimated = 0.0

        else:

            dso_estimated = (
                sum(recent_ar)
                / total_recent_credit_sales
                * 30
            )

            dso_estimated = clamp(
                dso_estimated,
                0,
                180
            )

        # ----------------------------------------------------
        # INVENTORY DAYS
        # ----------------------------------------------------

        if total_recent_cogs <= 0:

            inventory_days_estimated = 0.0

        else:

            inventory_days_estimated = (
                sum(recent_inventory)
                / total_recent_cogs
                * 30
            )

            inventory_days_estimated = clamp(
                inventory_days_estimated,
                0,
                180
            )

        # ----------------------------------------------------
        # DPO
        # ----------------------------------------------------

        if total_recent_credit_purchases <= 0:

            dpo_estimated = 0.0

        else:

            dpo_estimated = (
                sum(recent_ap)
                / total_recent_credit_purchases
                * 30
            )

            dpo_estimated = clamp(
                dpo_estimated,
                0,
                180
            )

        # ----------------------------------------------------
        # CASH CONVERSION CYCLE
        # ----------------------------------------------------

        cash_conversion_cycle = (
            dso_estimated
            + inventory_days_estimated
            - dpo_estimated
        )

        # Keep the derived metric bounded to a sensible
        # operational range.
        cash_conversion_cycle = clamp(
            cash_conversion_cycle,
            -180,
            360
        )

        # ====================================================
        # OUTPUT RECORD
        # ====================================================

        results.append(
            {
                "company_id":
                    company["company_id"],

                "month_index":
                    row["month_index"],

                "month":
                    row["month"],

                "revenue":
                    revenue,

                "cash_sales":
                    cash_sales,

                "credit_sales":
                    credit_sales,

                "collections":
                    collections,

                "accounts_receivable":
                    accounts_receivable,

                "cogs":
                    cogs,

                "beginning_inventory":
                    beginning_inventory,

                "purchases":
                    purchases,

                "cash_purchases":
                    cash_purchases,

                "credit_purchases":
                    credit_purchases,

                "inventory":
                    inventory,

                "supplier_payments":
                    supplier_payments,

                "accounts_payable":
                    accounts_payable,

                "dso":
                    dso_estimated,

                "inventory_days":
                    inventory_days_estimated,

                "dpo":
                    dpo_estimated,

                "cash_conversion_cycle":
                    cash_conversion_cycle,

                "cash_sales_pct":
                    cash_sales_pct,

                "cogs_margin":
                    cogs_margin,

                "target_inventory_days":
                    month_inventory_days,

                "target_dso":
                    month_dso_days,

                "target_dpo":
                    month_dpo_days,

                "shock_active":
                    bool(
                        shock.get(
                            "active",
                            False
                        )
                    ),

                "shock_type":
                    shock.get(
                        "shock_type",
                        "none"
                    ),

                "shock_severity":
                    shock.get(
                        "severity",
                        "none"
                    ),

                "expense_shock_multiplier":
                    shock.get(
                        "expense_multiplier",
                        1.0
                    ),

                "opening_ar":
                    opening_ar,

                "opening_inventory":
                    opening_inventory,

                "opening_ap":
                    opening_ap,
            }
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_working_capital_summary(
    results
):

    latest = results[-1]

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FINSHIELD WORKING CAPITAL ENGINE"
    )

    print(
        "=" * 70
    )

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

    print(
        "=" * 70
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from company_generator import (
        generate_companies
    )

    from revenue_engine import (
        generate_revenue_trajectory
    )

    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    revenue = generate_revenue_trajectory(
        company=company,
        months=36
    )

    results = simulate_working_capital(
        company=company,
        revenue_trajectory=revenue
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