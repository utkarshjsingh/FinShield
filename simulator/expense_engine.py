"""
FinShield - Expense Simulation Engine

Simulates monthly operating expenses for synthetic SMEs.

Expenses include:
    - Payroll
    - Rent
    - Utilities
    - Marketing
    - Insurance
    - Other operating expenses
    - Simplified tax provision

Important:
This is a financial simulation, not an Indian tax/accounting engine.
"""

import random

from config import RANDOM_SEED


# ============================================================
# RANDOM GENERATOR
# ============================================================

rng = random.Random(RANDOM_SEED + 300)


# ============================================================
# EXPENSE PROFILES
# ============================================================

EXPENSE_PROFILES = {

    "retail": {
        "monthly_employee_cost": (22_000, 45_000),
        "rent_pct_revenue": (0.03, 0.08),
        "utility_pct_revenue": (0.01, 0.025),
        "marketing_pct_revenue": (0.01, 0.04),
        "insurance_pct_revenue": (0.002, 0.008),
        "other_pct_revenue": (0.02, 0.06),
    },

    "wholesale": {
        "monthly_employee_cost": (25_000, 50_000),
        "rent_pct_revenue": (0.015, 0.045),
        "utility_pct_revenue": (0.005, 0.015),
        "marketing_pct_revenue": (0.005, 0.025),
        "insurance_pct_revenue": (0.002, 0.008),
        "other_pct_revenue": (0.015, 0.045),
    },

    "manufacturing": {
        "monthly_employee_cost": (25_000, 55_000),
        "rent_pct_revenue": (0.015, 0.05),
        "utility_pct_revenue": (0.02, 0.06),
        "marketing_pct_revenue": (0.005, 0.02),
        "insurance_pct_revenue": (0.003, 0.012),
        "other_pct_revenue": (0.02, 0.06),
    },

    "food_hospitality": {
        "monthly_employee_cost": (18_000, 40_000),
        "rent_pct_revenue": (0.05, 0.12),
        "utility_pct_revenue": (0.02, 0.05),
        "marketing_pct_revenue": (0.01, 0.04),
        "insurance_pct_revenue": (0.002, 0.008),
        "other_pct_revenue": (0.02, 0.06),
    },

    "professional_services": {
        "monthly_employee_cost": (35_000, 90_000),
        "rent_pct_revenue": (0.02, 0.06),
        "utility_pct_revenue": (0.005, 0.02),
        "marketing_pct_revenue": (0.01, 0.05),
        "insurance_pct_revenue": (0.002, 0.01),
        "other_pct_revenue": (0.015, 0.05),
    },
}


# ============================================================
# HELPER
# ============================================================

def uniform(low, high):
    return rng.uniform(low, high)


# ============================================================
# COMPANY EXPENSE PARAMETERS
# ============================================================

def generate_expense_parameters(company):
    """
    Generate company-specific expense parameters.

    These remain relatively stable throughout the simulation.
    """

    sector = company["sector"]

    profile = EXPENSE_PROFILES[sector]

    return {
        "employee_cost": uniform(
            *profile["monthly_employee_cost"]
        ),

        "rent_pct_revenue": uniform(
            *profile["rent_pct_revenue"]
        ),

        "utility_pct_revenue": uniform(
            *profile["utility_pct_revenue"]
        ),

        "marketing_pct_revenue": uniform(
            *profile["marketing_pct_revenue"]
        ),

        "insurance_pct_revenue": uniform(
            *profile["insurance_pct_revenue"]
        ),

        "other_pct_revenue": uniform(
            *profile["other_pct_revenue"]
        ),

        # Simplified effective tax assumption.
        # This is NOT an Indian tax calculation.
        "effective_tax_rate": uniform(
            0.20,
            0.25
        ),
    }


# ============================================================
# PAYROLL
# ============================================================

def calculate_payroll(
    employees,
    employee_cost,
):
    """
    Calculate monthly payroll.

    Payroll is relatively sticky and therefore does not
    immediately fall when revenue falls.
    """

    return (
        employees
        * employee_cost
    )


# ============================================================
# RENT
# ============================================================

def calculate_rent(
    revenue,
    rent_pct_revenue,
    location_factor,
):
    """
    Calculate rent.

    Location factor represents differences in operating
    cost across simulated business environments.
    """

    return (
        revenue
        * rent_pct_revenue
        * location_factor
    )


# ============================================================
# UTILITIES
# ============================================================

def calculate_utilities(
    revenue,
    utility_pct_revenue,
    sector,
):
    """
    Calculate utilities.

    Manufacturing and food/hospitality are generally
    more activity-intensive than professional services.
    """

    activity_factor = 1.0

    if sector == "manufacturing":
        activity_factor = 1.15

    elif sector == "food_hospitality":
        activity_factor = 1.10

    elif sector == "retail":
        activity_factor = 1.05

    return (
        revenue
        * utility_pct_revenue
        * activity_factor
    )


# ============================================================
# MARKETING
# ============================================================

def calculate_marketing(
    revenue,
    marketing_pct_revenue,
):
    """Calculate revenue-linked marketing expenditure."""

    return (
        revenue
        * marketing_pct_revenue
    )


# ============================================================
# INSURANCE
# ============================================================

def calculate_insurance(
    revenue,
    insurance_pct_revenue,
):
    """Calculate monthly insurance expense."""

    return (
        revenue
        * insurance_pct_revenue
    )


# ============================================================
# OTHER EXPENSES
# ============================================================

def calculate_other_expenses(
    revenue,
    other_pct_revenue,
):
    """
    Calculate miscellaneous operating expenses.
    """

    return (
        revenue
        * other_pct_revenue
    )


# ============================================================
# TAX PROVISION
# ============================================================

def calculate_tax_provision(
    operating_profit_before_tax,
    effective_tax_rate,
):
    """
    Calculate a simplified tax provision.

    IMPORTANT:
    This is only for synthetic simulation.

    We are NOT attempting to model:
        - GST
        - TDS
        - depreciation tax rules
        - MAT
        - surcharge
        - tax slabs
        - actual Indian corporate tax filing

    Those can be added later if required.
    """

    if operating_profit_before_tax <= 0:
        return 0.0

    return (
        operating_profit_before_tax
        * effective_tax_rate
    )


# ============================================================
# MAIN EXPENSE ENGINE
# ============================================================

def simulate_expenses(
    company,
    financial_trajectory,
):
    """
    Simulate monthly operating expenses.

    financial_trajectory must contain at least:
        month
        revenue
        cogs
    """

    parameters = generate_expense_parameters(
        company
    )

    results = []

    for row in financial_trajectory:

        revenue = row["revenue"]

        cogs = row.get(
            "cogs",
            0.0
        )

        # ----------------------------------------------------
        # PAYROLL
        # ----------------------------------------------------

        payroll = calculate_payroll(
            employees=company["employees"],
            employee_cost=parameters[
                "employee_cost"
            ],
        )

        # ----------------------------------------------------
        # RENT
        # ----------------------------------------------------

        rent = calculate_rent(
            revenue=revenue,
            rent_pct_revenue=parameters[
                "rent_pct_revenue"
            ],
            location_factor=company[
                "location_factor"
            ],
        )

        # ----------------------------------------------------
        # UTILITIES
        # ----------------------------------------------------

        utilities = calculate_utilities(
            revenue=revenue,
            utility_pct_revenue=parameters[
                "utility_pct_revenue"
            ],
            sector=company["sector"],
        )

        # ----------------------------------------------------
        # MARKETING
        # ----------------------------------------------------

        marketing = calculate_marketing(
            revenue=revenue,
            marketing_pct_revenue=parameters[
                "marketing_pct_revenue"
            ],
        )

        # ----------------------------------------------------
        # INSURANCE
        # ----------------------------------------------------

        insurance = calculate_insurance(
            revenue=revenue,
            insurance_pct_revenue=parameters[
                "insurance_pct_revenue"
            ],
        )

        # ----------------------------------------------------
        # OTHER OPERATING EXPENSES
        # ----------------------------------------------------

        other_expenses = calculate_other_expenses(
            revenue=revenue,
            other_pct_revenue=parameters[
                "other_pct_revenue"
            ],
        )

        # ----------------------------------------------------
        # OPERATING EXPENSES
        # ----------------------------------------------------

        operating_expenses = (
            payroll
            + rent
            + utilities
            + marketing
            + insurance
            + other_expenses
        )

        # ----------------------------------------------------
        # OPERATING PROFIT
        # ----------------------------------------------------

        operating_profit = (
            revenue
            - cogs
            - operating_expenses
        )

        # ----------------------------------------------------
        # TAX
        # ----------------------------------------------------

        tax_provision = (
            calculate_tax_provision(
                operating_profit,
                parameters[
                    "effective_tax_rate"
                ],
            )
        )

        profit_after_tax = (
            operating_profit
            - tax_provision
        )

        # ----------------------------------------------------
        # SAVE
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

                "cogs": cogs,

                "payroll": payroll,
                "rent": rent,
                "utilities": utilities,
                "marketing": marketing,
                "insurance": insurance,
                "other_expenses": other_expenses,

                "operating_expenses":
                    operating_expenses,

                "operating_profit":
                    operating_profit,

                "tax_provision":
                    tax_provision,

                "profit_after_tax":
                    profit_after_tax,

                # Store parameters for transparency.
                "employee_cost":
                    parameters[
                        "employee_cost"
                    ],

                "effective_tax_rate":
                    parameters[
                        "effective_tax_rate"
                    ],
            }
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_expense_summary(results):

    latest = results[-1]

    print("\n" + "=" * 70)
    print("FINSHIELD EXPENSE ENGINE")
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
        f"COGS: "
        f"₹{latest['cogs']:,.0f}"
    )

    print(
        f"Payroll: "
        f"₹{latest['payroll']:,.0f}"
    )

    print(
        f"Rent: "
        f"₹{latest['rent']:,.0f}"
    )

    print(
        f"Utilities: "
        f"₹{latest['utilities']:,.0f}"
    )

    print(
        f"Marketing: "
        f"₹{latest['marketing']:,.0f}"
    )

    print(
        f"Insurance: "
        f"₹{latest['insurance']:,.0f}"
    )

    print(
        f"Other expenses: "
        f"₹{latest['other_expenses']:,.0f}"
    )

    print(
        f"Operating expenses: "
        f"₹{latest['operating_expenses']:,.0f}"
    )

    print(
        f"Operating profit: "
        f"₹{latest['operating_profit']:,.0f}"
    )

    print(
        f"Tax provision: "
        f"₹{latest['tax_provision']:,.0f}"
    )

    print(
        f"Profit after tax: "
        f"₹{latest['profit_after_tax']:,.0f}"
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

    from working_capital import (
        simulate_working_capital,
    )

    # --------------------------------------------------------
    # Generate one company
    # --------------------------------------------------------

    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    revenue_trajectory = (
        generate_revenue_trajectory(
            company=company,
            months=36,
        )
    )

    # --------------------------------------------------------
    # Working capital
    # --------------------------------------------------------

    working_capital = (
        simulate_working_capital(
            company=company,
            revenue_trajectory=revenue_trajectory,
        )
    )

    # --------------------------------------------------------
    # Expense engine requires revenue + COGS.
    #
    # Working capital already contains COGS,
    # so we combine the information here.
    # --------------------------------------------------------

    expenses = (
        simulate_expenses(
            company=company,
            financial_trajectory=working_capital,
        )
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
        f"Employees: "
        f"{company['employees']}"
    )

    print_expense_summary(
        expenses
    )