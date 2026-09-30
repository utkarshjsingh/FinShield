"""
FinShield - Expense Simulation Engine

Simulates operating expenses while keeping sector economics
financially coherent.

Expenses:
    - Payroll
    - Rent
    - Utilities
    - Marketing
    - Insurance
    - Other operating expenses
    - Tax provision

Tax is a simplified accounting provision.
Actual cash tax timing is handled later.
"""

import random

from config import RANDOM_SEED


rng = random.Random(RANDOM_SEED + 300)


# ============================================================
# EXPENSE PROFILES
# ============================================================

EXPENSE_PROFILES = {

    "retail": {
        "monthly_employee_cost": (22_000, 40_000),

        "rent_pct_revenue": (
            0.025,
            0.055
        ),

        "utility_pct_revenue": (
            0.008,
            0.018
        ),

        "marketing_pct_revenue": (
            0.008,
            0.025
        ),

        "insurance_pct_revenue": (
            0.002,
            0.006
        ),

        "other_pct_revenue": (
            0.015,
            0.035
        ),
    },

    "wholesale": {
        "monthly_employee_cost": (
            25_000,
            45_000
        ),

        "rent_pct_revenue": (
            0.012,
            0.030
        ),

        "utility_pct_revenue": (
            0.004,
            0.012
        ),

        "marketing_pct_revenue": (
            0.004,
            0.015
        ),

        "insurance_pct_revenue": (
            0.002,
            0.006
        ),

        "other_pct_revenue": (
            0.012,
            0.030
        ),
    },

    "manufacturing": {
        "monthly_employee_cost": (
            25_000,
            50_000
        ),

        "rent_pct_revenue": (
            0.012,
            0.035
        ),

        "utility_pct_revenue": (
            0.015,
            0.040
        ),

        "marketing_pct_revenue": (
            0.003,
            0.015
        ),

        "insurance_pct_revenue": (
            0.003,
            0.008
        ),

        "other_pct_revenue": (
            0.015,
            0.040
        ),
    },

    "food_hospitality": {
        "monthly_employee_cost": (
            18_000,
            35_000
        ),

        "rent_pct_revenue": (
            0.045,
            0.090
        ),

        "utility_pct_revenue": (
            0.015,
            0.035
        ),

        "marketing_pct_revenue": (
            0.008,
            0.025
        ),

        "insurance_pct_revenue": (
            0.002,
            0.006
        ),

        "other_pct_revenue": (
            0.015,
            0.040
        ),
    },

    "professional_services": {
        "monthly_employee_cost": (
            35_000,
            75_000
        ),

        "rent_pct_revenue": (
            0.015,
            0.045
        ),

        "utility_pct_revenue": (
            0.004,
            0.015
        ),

        "marketing_pct_revenue": (
            0.008,
            0.035
        ),

        "insurance_pct_revenue": (
            0.002,
            0.008
        ),

        "other_pct_revenue": (
            0.012,
            0.035
        ),
    },
}


# ============================================================
# HELPERS
# ============================================================

def uniform(low, high):
    return rng.uniform(low, high)


# ============================================================
# PARAMETERS
# ============================================================

def generate_expense_parameters(company):

    profile = EXPENSE_PROFILES[
        company["sector"]
    ]

    return {

        "employee_cost":
            uniform(
                *profile[
                    "monthly_employee_cost"
                ]
            ),

        "rent_pct_revenue":
            uniform(
                *profile[
                    "rent_pct_revenue"
                ]
            ),

        "utility_pct_revenue":
            uniform(
                *profile[
                    "utility_pct_revenue"
                ]
            ),

        "marketing_pct_revenue":
            uniform(
                *profile[
                    "marketing_pct_revenue"
                ]
            ),

        "insurance_pct_revenue":
            uniform(
                *profile[
                    "insurance_pct_revenue"
                ]
            ),

        "other_pct_revenue":
            uniform(
                *profile[
                    "other_pct_revenue"
                ]
            ),

        "effective_tax_rate":
            uniform(
                0.20,
                0.25
            ),
    }


# ============================================================
# EXPENSE FUNCTIONS
# ============================================================

def calculate_payroll(
    employees,
    employee_cost
):

    return (
        employees
        * employee_cost
    )


def calculate_rent(
    revenue,
    rent_pct_revenue,
    location_factor
):

    return (
        revenue
        * rent_pct_revenue
        * location_factor
    )


def calculate_utilities(
    revenue,
    utility_pct_revenue,
    sector
):

    factor = 1.0

    if sector == "manufacturing":
        factor = 1.10

    elif sector == "food_hospitality":
        factor = 1.08

    elif sector == "retail":
        factor = 1.03

    return (
        revenue
        * utility_pct_revenue
        * factor
    )


def calculate_marketing(
    revenue,
    marketing_pct_revenue
):

    return (
        revenue
        * marketing_pct_revenue
    )


def calculate_insurance(
    revenue,
    insurance_pct_revenue
):

    return (
        revenue
        * insurance_pct_revenue
    )


def calculate_other_expenses(
    revenue,
    other_pct_revenue
):

    return (
        revenue
        * other_pct_revenue
    )


def calculate_tax_provision(
    operating_profit_before_tax,
    effective_tax_rate
):

    if operating_profit_before_tax <= 0:
        return 0.0

    return (
        operating_profit_before_tax
        * effective_tax_rate
    )


# ============================================================
# MAIN ENGINE
# ============================================================

def simulate_expenses(
    company,
    financial_trajectory
):

    parameters = (
        generate_expense_parameters(
            company
        )
    )

    results = []

    for row in financial_trajectory:

        revenue = row["revenue"]
        cogs = row["cogs"]

        payroll = calculate_payroll(
            company["employees"],
            parameters[
                "employee_cost"
            ]
        )

        rent = calculate_rent(
            revenue,
            parameters[
                "rent_pct_revenue"
            ],
            company[
                "location_factor"
            ]
        )

        utilities = calculate_utilities(
            revenue,
            parameters[
                "utility_pct_revenue"
            ],
            company["sector"]
        )

        marketing = calculate_marketing(
            revenue,
            parameters[
                "marketing_pct_revenue"
            ]
        )

        insurance = calculate_insurance(
            revenue,
            parameters[
                "insurance_pct_revenue"
            ]
        )

        other_expenses = (
            calculate_other_expenses(
                revenue,
                parameters[
                    "other_pct_revenue"
                ]
            )
        )

        operating_expenses = (
            payroll
            + rent
            + utilities
            + marketing
            + insurance
            + other_expenses
        )

        operating_profit = (
            revenue
            - cogs
            - operating_expenses
        )

        tax_provision = (
            calculate_tax_provision(
                operating_profit,
                parameters[
                    "effective_tax_rate"
                ]
            )
        )

        profit_after_tax = (
            operating_profit
            - tax_provision
        )

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

                "cogs":
                    cogs,

                "payroll":
                    payroll,

                "rent":
                    rent,

                "utilities":
                    utilities,

                "marketing":
                    marketing,

                "insurance":
                    insurance,

                "other_expenses":
                    other_expenses,

                "operating_expenses":
                    operating_expenses,

                "operating_profit":
                    operating_profit,

                "tax_provision":
                    tax_provision,

                "profit_after_tax":
                    profit_after_tax,

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

def print_expense_summary(
    results
):

    latest = results[-1]

    print("\n" + "=" * 70)
    print(
        "FINSHIELD EXPENSE ENGINE"
    )
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
        generate_companies
    )

    from revenue_engine import (
        generate_revenue_trajectory
    )

    from working_capital import (
        simulate_working_capital
    )

    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    revenue = generate_revenue_trajectory(
        company=company,
        months=36
    )

    working_capital = (
        simulate_working_capital(
            company=company,
            revenue_trajectory=revenue
        )
    )

    expenses = simulate_expenses(
        company=company,
        financial_trajectory=working_capital
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