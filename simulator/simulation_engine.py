"""
FinShield - Master Simulation Engine

Orchestrates the complete SME financial simulation:

    Company Generator
          ↓
    Revenue Engine
          ↓
    Working Capital Engine
          ↓
    Expense Engine
          ↓
    Debt Engine
          ↓
    Cash Flow Engine
          ↓
    Complete Monthly Financial Dataset

Prototype:
    50 companies × 36 months = 1,800 rows

Later:
    10,000 companies × 36 months = 360,000 rows
    100,000 companies × 36 months = 3,600,000 rows
"""

import csv
from pathlib import Path

from config import (
    ACTIVE_COMPANIES,
    HISTORY_MONTHS,
)

from company_generator import (
    generate_companies,
)

from revenue_engine import (
    generate_revenue_trajectory,
)

from shock_engine import (
    generate_shock_schedule,
)

from working_capital import (
    simulate_working_capital,
)

from expense_engine import (
    simulate_expenses,
)

from debt_engine import (
    generate_debt_schedule,
)

from cash_engine import (
    simulate_cash_flow,
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "monthly_financials.csv"
)


# ============================================================
# SIMULATE ONE COMPANY
# ============================================================

def simulate_company(
    company,
    months=HISTORY_MONTHS,
):
    """
    Run every FinShield engine for one company.

    Returns
    -------
    list of dict
        One dictionary per company-month.
    """

    # --------------------------------------------------------
    # 1. SHOCK SCHEDULE
    # --------------------------------------------------------

    shock_schedule = generate_shock_schedule(
        company=company,
        months=months,
    )

    # --------------------------------------------------------
    # 2. REVENUE
    # --------------------------------------------------------

    revenue_trajectory = (
        generate_revenue_trajectory(
            company=company,
            months=months,
            shock_schedule=shock_schedule,
        )
    )

    # --------------------------------------------------------
    # 3. WORKING CAPITAL
    # --------------------------------------------------------

    working_capital = (
        simulate_working_capital(
            company=company,
            revenue_trajectory=revenue_trajectory,
            shock_schedule=shock_schedule,
        )
    )

    # --------------------------------------------------------
    # 4. EXPENSES
    # --------------------------------------------------------

    expenses = simulate_expenses(
        company=company,
        financial_trajectory=working_capital,
    )

    # --------------------------------------------------------
    # 5. DEBT
    # --------------------------------------------------------

    loan, debt_schedule = (
        generate_debt_schedule(
            company=company,
            months=months,
        )
    )

    # --------------------------------------------------------
    # 6. CASH FLOW
    # --------------------------------------------------------

    cash_flow = simulate_cash_flow(
        company=company,
        working_capital=working_capital,
        expenses=expenses,
        debt_schedule=debt_schedule,
    )

    # --------------------------------------------------------
    # SANITY CHECK
    # --------------------------------------------------------

    if not (
        len(revenue_trajectory)
        == len(working_capital)
        == len(expenses)
        == len(debt_schedule)
        == len(cash_flow)
    ):
        raise ValueError(
            f"Trajectory length mismatch for "
            f"{company['company_id']}"
        )

    # --------------------------------------------------------
    # COMBINE EVERYTHING
    # --------------------------------------------------------

    monthly_records = []

    for i in range(months):

        revenue = revenue_trajectory[i]
        wc = working_capital[i]
        exp = expenses[i]
        debt = debt_schedule[i]
        cash = cash_flow[i]
        shock = shock_schedule[i]

        record = {

            # =================================================
            # COMPANY IDENTIFICATION
            # =================================================

            "company_id":
                company["company_id"],

            "sector":
                company["sector"],

            "company_size":
                company["company_size"],

            "subtype":
                company["subtype"],

            "employees":
                company["employees"],

            # =================================================
            # COMPANY STATIC FINANCIAL CHARACTERISTICS
            # =================================================

            "annual_base_revenue":
                company["annual_revenue"],

            "starting_cash":
                company["starting_cash"],

            "initial_debt":
                company["debt_balance"],

            "credit_limit":
                company["credit_limit"],

            "customer_concentration":
                company[
                    "customer_concentration"
                ],

            "location_factor":
                company[
                    "location_factor"
                ],

            # =================================================
            # TIME
            # =================================================

            "month_index":
                i,

            "month":
                revenue["month"],

            # =================================================
            # REVENUE
            # =================================================

            "revenue":
                revenue["revenue"],

            "seasonality":
                revenue.get(
                    "seasonality",
                    1.0,
                ),

            # =================================================
            # SHOCK METADATA
            # =================================================

            "shock_active":
                bool(shock.get("active", False)),

            "shock_type":
                shock.get("shock_type", "none"),

            "shock_severity":
                shock.get("severity", "none"),

            "revenue_shock_multiplier":
                shock.get("revenue_multiplier", 1.0),

            "dso_shock_multiplier":
                shock.get("dso_multiplier", 1.0),

            "inventory_shock_multiplier":
                shock.get("inventory_multiplier", 1.0),

            "cogs_shock_multiplier":
                shock.get("cogs_multiplier", 1.0),

            "dpo_shock_multiplier":
                shock.get("dpo_multiplier", 1.0),

            "expense_shock_multiplier":
                shock.get("expense_multiplier", 1.0),

            # =================================================
            # WORKING CAPITAL
            # =================================================

            "cash_sales":
                wc["cash_sales"],

            "credit_sales":
                wc["credit_sales"],

            "collections":
                wc["collections"],

            "accounts_receivable":
                wc[
                    "accounts_receivable"
                ],

            "cogs":
                wc["cogs"],

            "purchases":
                wc["purchases"],

            "cash_purchases":
                wc["cash_purchases"],

            "credit_purchases":
                wc["credit_purchases"],

            "inventory":
                wc["inventory"],

            "supplier_payments":
                wc[
                    "supplier_payments"
                ],

            "accounts_payable":
                wc[
                    "accounts_payable"
                ],

            # =================================================
            # WORKING CAPITAL METRICS
            # =================================================

            "dso":
                wc["dso"],

            "inventory_days":
                wc[
                    "inventory_days"
                ],

            "dpo":
                wc["dpo"],

            "cash_conversion_cycle":
                wc[
                    "cash_conversion_cycle"
                ],

            # =================================================
            # EXPENSES
            # =================================================

            "payroll":
                exp["payroll"],

            "rent":
                exp["rent"],

            "utilities":
                exp["utilities"],

            "marketing":
                exp["marketing"],

            "insurance":
                exp["insurance"],

            "other_expenses":
                exp["other_expenses"],

            "operating_expenses":
                exp[
                    "operating_expenses"
                ],

            "operating_profit":
                exp[
                    "operating_profit"
                ],

            "tax_provision":
                exp[
                    "tax_provision"
                ],

            "profit_after_tax":
                exp[
                    "profit_after_tax"
                ],

            # =================================================
            # DEBT
            # =================================================

            "loan_principal":
                debt[
                    "principal_payment"
                ],

            "loan_interest":
                debt[
                    "interest_payment"
                ],

            "loan_payment":
    (
        debt["principal_payment"]
        + debt["interest_payment"]
    ),

            "debt_balance":
                debt[
                    "ending_debt_balance"
                ],

            # =================================================
            # CASH FLOW
            # =================================================

            "beginning_cash":
                cash[
                    "beginning_cash"
                ],

            "operating_inflows":
                cash[
                    "operating_inflows"
                ],

            "total_cash_outflow":
                cash[
                    "total_cash_outflow"
                ],

            "cash_before_financing":
                cash[
                    "cash_before_financing"
                ],

            "credit_draw":
                cash[
                    "credit_draw"
                ],

            "credit_repayment":
                cash[
                    "credit_repayment"
                ],

            "ending_cash":
                cash[
                    "ending_cash"
                ],

            # =================================================
            # LIQUIDITY
            # =================================================

            "credit_balance":
                cash[
                    "ending_credit_balance"
                ],

            "available_credit":
                cash[
                    "available_credit"
                ],

            "available_liquidity":
                cash[
                    "available_liquidity"
                ],

            "unfunded_deficit":
                cash[
                    "unfunded_deficit"
                ],

            "net_cash_flow":
                cash[
                    "net_cash_flow"
                ],
        }

        monthly_records.append(
            record
        )

    return monthly_records


# ============================================================
# SIMULATE ALL COMPANIES
# ============================================================

def simulate_all_companies(
    total_companies=ACTIVE_COMPANIES,
    months=HISTORY_MONTHS,
):
    """
    Generate companies and simulate each one.

    Returns
    -------
    list of dict
        Complete company-month dataset.
    """

    print("\n" + "=" * 75)
    print(
        "FINSHIELD MASTER SIMULATION ENGINE"
    )
    print("=" * 75)

    print(
        f"\nCompanies: "
        f"{total_companies}"
    )

    print(
        f"Months per company: "
        f"{months}"
    )

    print(
        f"Expected rows: "
        f"{total_companies * months:,}"
    )

    print(
        "\nGenerating companies..."
    )

    companies = generate_companies(
        total_companies=total_companies
    )

    print(
        f"Companies generated: "
        f"{len(companies)}"
    )

    all_records = []

    # --------------------------------------------------------
    # SIMULATE
    # --------------------------------------------------------

    for index, company in enumerate(
        companies,
        start=1,
    ):

        records = simulate_company(
            company=company,
            months=months,
        )

        all_records.extend(
            records
        )

        # Progress every 10 companies.
        if (
            index % 10 == 0
            or index == len(companies)
        ):

            print(
                f"  Simulated "
                f"{index}/{len(companies)} "
                f"companies"
            )

    print(
        f"\nTotal monthly records: "
        f"{len(all_records):,}"
    )

    return (
        companies,
        all_records,
    )


# ============================================================
# SAVE MONTHLY DATA
# ============================================================

def save_monthly_financials(
    records,
):
    """
    Save complete company-month dataset.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not records:
        raise ValueError(
            "No records to save."
        )

    fieldnames = list(
        records[0].keys()
    )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            records
        )

    return OUTPUT_FILE


# ============================================================
# VALIDATION
# ============================================================

def validate_dataset(
    records,
    expected_companies,
    expected_months,
):
    """
    Basic structural validation.

    This is NOT statistical calibration yet.
    It only verifies that the simulation produced
    the expected structure.
    """

    expected_rows = (
        expected_companies
        * expected_months
    )

    print(
        "\n" + "=" * 75
    )

    print(
        "DATASET VALIDATION"
    )

    print(
        "=" * 75
    )

    print(
        f"Expected rows: "
        f"{expected_rows:,}"
    )

    print(
        f"Actual rows:   "
        f"{len(records):,}"
    )

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    assert (
        len(records)
        == expected_rows
    ), (
        "Unexpected number of rows."
    )

    # --------------------------------------------------------
    # Unique companies
    # --------------------------------------------------------

    company_ids = {
        row["company_id"]
        for row in records
    }

    print(
        f"Unique companies: "
        f"{len(company_ids):,}"
    )

    assert (
        len(company_ids)
        == expected_companies
    )

    # --------------------------------------------------------
    # Months per company
    # --------------------------------------------------------

    company_month_counts = {}

    for row in records:

        company_id = row[
            "company_id"
        ]

        company_month_counts[
            company_id
        ] = (
            company_month_counts.get(
                company_id,
                0,
            )
            + 1
        )

    invalid_companies = [
        company_id
        for company_id, count
        in company_month_counts.items()
        if count != expected_months
    ]

    print(
        f"Companies with incorrect "
        f"month count: "
        f"{len(invalid_companies)}"
    )

    assert not invalid_companies

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = {

        "company_id",
        "sector",
        "company_size",
        "month",

        "revenue",
        "cogs",

        "accounts_receivable",
        "inventory",
        "accounts_payable",

        "operating_expenses",
        "operating_profit",

        "debt_balance",

        "beginning_cash",
        "ending_cash",

        "credit_balance",
        "available_credit",

        "available_liquidity",
        "unfunded_deficit",
    }

    actual_columns = set(
        records[0].keys()
    )

    missing_columns = (
        required_columns
        - actual_columns
    )

    print(
        f"Missing required columns: "
        f"{len(missing_columns)}"
    )

    assert not missing_columns

    # --------------------------------------------------------
    # Negative values
    # --------------------------------------------------------

    negative_cash = sum(
        1
        for row in records
        if row["ending_cash"] < 0
    )

    negative_inventory = sum(
        1
        for row in records
        if row["inventory"] < 0
    )

    negative_ar = sum(
        1
        for row in records
        if row["accounts_receivable"] < 0
    )

    negative_ap = sum(
        1
        for row in records
        if row["accounts_payable"] < 0
    )

    print(
        f"Negative ending cash rows: "
        f"{negative_cash}"
    )

    print(
        f"Negative inventory rows: "
        f"{negative_inventory}"
    )

    print(
        f"Negative AR rows: "
        f"{negative_ar}"
    )

    print(
        f"Negative AP rows: "
        f"{negative_ap}"
    )

    # Cash/inventory/AR/AP should never be negative.
    assert negative_cash == 0
    assert negative_inventory == 0
    assert negative_ar == 0
    assert negative_ap == 0

    # --------------------------------------------------------
    # Unfunded deficit
    # --------------------------------------------------------

    deficit_rows = sum(
        1
        for row in records
        if row["unfunded_deficit"] > 0
    )

    print(
        f"Rows with unfunded deficit: "
        f"{deficit_rows:,}"
    )

    print(
        "\nStructural validation PASSED."
    )

    print(
        "=" * 75
    )


# ============================================================
# SUMMARY
# ============================================================

def print_dataset_summary(
    records,
):

    if not records:
        return

    companies = {
        row["company_id"]
        for row in records
    }

    sectors = {}

    sizes = {}

    total_deficit = 0.0

    total_revenue = 0.0

    for row in records:

        sector = row[
            "sector"
        ]

        size = row[
            "company_size"
        ]

        sectors[
            sector
        ] = sectors.get(
            sector,
            0,
        ) + 1

        sizes[
            size
        ] = sizes.get(
            size,
            0,
        ) + 1

        total_deficit += (
            row[
                "unfunded_deficit"
            ]
        )

        total_revenue += (
            row["revenue"]
        )

    print(
        "\n" + "=" * 75
    )

    print(
        "SIMULATION SUMMARY"
    )

    print(
        "=" * 75
    )

    print(
        f"Companies: "
        f"{len(companies):,}"
    )

    print(
        f"Monthly observations: "
        f"{len(records):,}"
    )

    print(
        f"Total simulated revenue: "
        f"₹{total_revenue:,.0f}"
    )

    print(
        f"Total unfunded deficit: "
        f"₹{total_deficit:,.0f}"
    )

    print(
        "\nSector observations:"
    )

    for sector, count in (
        sorted(sectors.items())
    ):

        print(
            f"  {sector:<25}"
            f"{count:,}"
        )

    print(
        "\nSize observations:"
    )

    for size, count in (
        sorted(sizes.items())
    ):

        print(
            f"  {size:<25}"
            f"{count:,}"
        )

    print(
        "=" * 75
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    companies, records = (
    simulate_all_companies(
        total_companies=ACTIVE_COMPANIES,
        months=HISTORY_MONTHS,
    )
)

    validate_dataset(
    records=records,
    expected_companies=(
        ACTIVE_COMPANIES
    ),
    expected_months=(
        HISTORY_MONTHS
    ),
)

    output_file = (
        save_monthly_financials(
            records
        )
    )

    print_dataset_summary(
        records
    )

    print(
        f"\nDataset saved to:"
    )

    print(
        f"  {output_file}"
    )

    print(
        "\nFinShield master simulation "
        "completed successfully."
    )