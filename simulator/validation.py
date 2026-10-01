"""
FinShield - Financial Realism Validation

Validates the synthetic SME population before scaling.

This checks:
    - Revenue distribution
    - Profitability
    - Cash flow
    - Debt burden
    - Credit utilization
    - Working capital
    - Liquidity stress
    - Sector/size differences

This is a sanity check, NOT the ML ground-truth generator.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = Path(
    "data/raw/monthly_financials.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Run simulation_engine.py first."
        )

    df = pd.read_csv(
        DATA_FILE
    )

    # --------------------------------------------------------
    # Derived validation metric
    # --------------------------------------------------------

    df["credit_utilization"] = (
        df["credit_balance"]
        / df["credit_limit"]
        .replace(0, float("nan"))
    )

    return df


# ============================================================
# BASIC DATA CHECK
# ============================================================

def basic_check(df):

    print("\n" + "=" * 75)
    print("BASIC DATA CHECK")
    print("=" * 75)

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print(
        f"Companies: "
        f"{df['company_id'].nunique():,}"
    )

    print(
        f"Months: "
        f"{df['month'].nunique():,}"
    )

    expected_columns = {
        "company_id",
        "sector",
        "company_size",
        "month",
        "revenue",
        "cogs",
        "operating_expenses",
        "operating_profit",
        "profit_after_tax",
        "accounts_receivable",
        "inventory",
        "accounts_payable",
        "dso",
        "dpo",
        "inventory_days",
        "cash_conversion_cycle",
        "debt_balance",
        "ending_cash",
        "credit_balance",
        "credit_limit",
        "available_credit",
        "available_liquidity",
        "unfunded_deficit",
        "net_cash_flow",
    }

    missing = (
        expected_columns
        - set(df.columns)
    )

    if missing:

        print(
            "\nWARNING - Missing columns:"
        )

        for column in sorted(missing):
            print(
                f"  {column}"
            )

    else:

        print(
            "All required columns present: YES"
        )


# ============================================================
# REVENUE
# ============================================================

def revenue_analysis(df):

    print("\n" + "=" * 75)
    print("REVENUE DISTRIBUTION")
    print("=" * 75)

    company_revenue = (
        df.groupby("company_id")
        ["revenue"]
        .sum()
        / 3
    )

    print(
        "\nApproximate annual revenue:"
    )

    print(
        company_revenue.describe()
        .to_string()
    )

    print(
        "\nBy sector:"
    )

    sector = (
        df.groupby("sector")
        ["revenue"]
        .mean()
        .sort_values()
    )

    print(
        sector.to_string()
    )

    print(
        "\nBy size:"
    )

    size = (
        df.groupby("company_size")
        ["revenue"]
        .mean()
        .sort_values()
    )

    print(
        size.to_string()
    )


# ============================================================
# PROFITABILITY
# ============================================================

def profitability_analysis(df):

    print("\n" + "=" * 75)
    print("PROFITABILITY")
    print("=" * 75)

    df = df.copy()

    df["operating_margin"] = (
        df["operating_profit"]
        / df["revenue"].clip(lower=1)
    )

    df["net_margin"] = (
        df["profit_after_tax"]
        / df["revenue"].clip(lower=1)
    )

    print(
        "\nOperating margin:"
    )

    print(
        df["operating_margin"]
        .describe()
        .to_string()
    )

    print(
        "\nNet margin:"
    )

    print(
        df["net_margin"]
        .describe()
        .to_string()
    )

    negative_profit = (
        df["operating_profit"] < 0
    ).mean()

    print(
        f"\nRows with negative "
        f"operating profit: "
        f"{negative_profit * 100:.2f}%"
    )

    print(
        "\nOperating margin by sector:"
    )

    sector_margin = (
        df.groupby("sector")
        ["operating_margin"]
        .mean()
        .sort_values()
    )

    print(
        sector_margin.to_string()
    )


# ============================================================
# LIQUIDITY
# ============================================================

def liquidity_analysis(df):

    print("\n" + "=" * 75)
    print("LIQUIDITY")
    print("=" * 75)

    deficit_rows = (
        df["unfunded_deficit"] > 0
    ).sum()

    deficit_pct = (
        deficit_rows
        / len(df)
        * 100
    )

    print(
        f"Rows with unfunded deficit: "
        f"{deficit_rows:,} "
        f"({deficit_pct:.2f}%)"
    )

    total_deficit = (
        df["unfunded_deficit"]
        .sum()
    )

    print(
        f"Total unfunded deficit: "
        f"₹{total_deficit:,.0f}"
    )

    print(
        "\nAvailable liquidity:"
    )

    print(
        df["available_liquidity"]
        .describe()
        .to_string()
    )

    print(
        "\nEnding cash:"
    )

    print(
        df["ending_cash"]
        .describe()
        .to_string()
    )


# ============================================================
# CREDIT UTILIZATION
# ============================================================

def credit_analysis(df):

    print("\n" + "=" * 75)
    print("CREDIT UTILIZATION")
    print("=" * 75)

    print(
        df["credit_utilization"]
        .describe()
        .to_string()
    )

    print(
        f"\n>50% utilization: "
        f"{(df['credit_utilization'] > 0.50).mean() * 100:.2f}%"
    )

    print(
        f">80% utilization: "
        f"{(df['credit_utilization'] > 0.80).mean() * 100:.2f}%"
    )

    print(
        f">95% utilization: "
        f"{(df['credit_utilization'] > 0.95).mean() * 100:.2f}%"
    )


# ============================================================
# DEBT
# ============================================================

def debt_analysis(df):

    print("\n" + "=" * 75)
    print("DEBT BURDEN")
    print("=" * 75)

    df = df.copy()

    df["debt_to_revenue"] = (
        df["debt_balance"]
        / df["revenue"].clip(lower=1)
    )

    print(
        "Debt / monthly revenue:"
    )

    print(
        df["debt_to_revenue"]
        .describe()
        .to_string()
    )

    print(
        "\nDebt balance:"
    )

    print(
        df["debt_balance"]
        .describe()
        .to_string()
    )


# ============================================================
# WORKING CAPITAL
# ============================================================

def working_capital_analysis(df):

    print("\n" + "=" * 75)
    print("WORKING CAPITAL")
    print("=" * 75)

    metrics = [
        "dso",
        "dpo",
        "inventory_days",
        "cash_conversion_cycle",
    ]

    for metric in metrics:

        print(
            f"\n{metric}:"
        )

        print(
            df[metric]
            .describe()
            .to_string()
        )

    print(
        "\nAverage metrics by sector:"
    )

    sector_wc = (
        df.groupby("sector")[
            metrics
        ]
        .mean()
    )

    print(
        sector_wc.to_string()
    )


# ============================================================
# CASH FLOW
# ============================================================

def cash_flow_analysis(df):

    print("\n" + "=" * 75)
    print("CASH FLOW")
    print("=" * 75)

    df = df.copy()

    df["cash_flow_margin"] = (
        df["net_cash_flow"]
        / df["revenue"].clip(lower=1)
    )

    print(
        "Net cash flow:"
    )

    print(
        df["net_cash_flow"]
        .describe()
        .to_string()
    )

    print(
        "\nCash-flow margin:"
    )

    print(
        df["cash_flow_margin"]
        .describe()
        .to_string()
    )

    negative_cash_flow = (
        df["net_cash_flow"] < 0
    ).mean()

    print(
        f"\nNegative cash-flow rows: "
        f"{negative_cash_flow * 100:.2f}%"
    )


# ============================================================
# SECTOR STRESS
# ============================================================

def sector_stress_analysis(df):

    print("\n" + "=" * 75)
    print("SECTOR STRESS")
    print("=" * 75)

    result = (
        df.groupby("sector")
        .agg(
            companies=(
                "company_id",
                "nunique"
            ),

            avg_revenue=(
                "revenue",
                "mean"
            ),

            avg_cash=(
                "ending_cash",
                "mean"
            ),

            avg_liquidity=(
                "available_liquidity",
                "mean"
            ),

            avg_dso=(
                "dso",
                "mean"
            ),

            avg_ccc=(
                "cash_conversion_cycle",
                "mean"
            ),

            deficit_rate=(
                "unfunded_deficit",
                lambda x: (
                    x > 0
                ).mean()
            ),

            avg_credit_utilization=(
                "credit_utilization",
                "mean"
            ),
        )
    )

    print(
        result.to_string()
    )


# ============================================================
# SIZE STRESS
# ============================================================

def size_stress_analysis(df):

    print("\n" + "=" * 75)
    print("SIZE STRESS")
    print("=" * 75)

    result = (
        df.groupby("company_size")
        .agg(
            companies=(
                "company_id",
                "nunique"
            ),

            avg_revenue=(
                "revenue",
                "mean"
            ),

            avg_cash=(
                "ending_cash",
                "mean"
            ),

            avg_liquidity=(
                "available_liquidity",
                "mean"
            ),

            deficit_rate=(
                "unfunded_deficit",
                lambda x: (
                    x > 0
                ).mean()
            ),

            avg_dso=(
                "dso",
                "mean"
            ),

            avg_ccc=(
                "cash_conversion_cycle",
                "mean"
            ),
        )
    )

    print(
        result.to_string()
    )


# ============================================================
# COMPANY-LEVEL DISTRESS
# ============================================================

def company_distress_analysis(df):

    print("\n" + "=" * 75)
    print("COMPANY-LEVEL LIQUIDITY STRESS")
    print("=" * 75)

    company_summary = (
        df.groupby("company_id")
        .agg(
            sector=(
                "sector",
                "first"
            ),

            size=(
                "company_size",
                "first"
            ),

            minimum_cash=(
                "ending_cash",
                "min"
            ),

            maximum_credit_utilization=(
                "credit_utilization",
                "max"
            ),

            maximum_deficit=(
                "unfunded_deficit",
                "max"
            ),

            minimum_liquidity=(
                "available_liquidity",
                "min"
            ),

            negative_cash_flow_months=(
                "net_cash_flow",
                lambda x: (
                    x < 0
                ).sum()
            ),
        )
    )

    

    company_count = len(
        company_summary
    )

    companies_with_deficit = (
        company_summary[
            "maximum_deficit"
        ] > 0
    ).sum()

    companies_high_credit = (
        company_summary[
            "maximum_credit_utilization"
        ] > 0.80
    ).sum()

    companies_cash_exhausted = (
        company_summary[
            "minimum_cash"
        ] <= 0
    ).sum()

    print(
        f"Total companies: "
        f"{company_count}"
    )

    print(
        f"Companies with unfunded deficit: "
        f"{companies_with_deficit} "
        f"({companies_with_deficit / company_count * 100:.2f}%)"
    )

    print(
        f"Companies reaching >80% credit utilization: "
        f"{companies_high_credit} "
        f"({companies_high_credit / company_count * 100:.2f}%)"
    )

    print(
        f"Companies reaching zero cash: "
        f"{companies_cash_exhausted} "
        f"({companies_cash_exhausted / company_count * 100:.2f}%)"
    )

    print(
        "\nCompany-level stress by sector:"
    )

    sector_summary = (
        company_summary
        .groupby("sector")
        .agg(
            companies=(
                "maximum_deficit",
                "count"
            ),

            deficit_companies=(
                "maximum_deficit",
                lambda x: (
                    x > 0
                ).sum()
            ),

            high_credit_companies=(
                "maximum_credit_utilization",
                lambda x: (
                    x > 0.80
                ).sum()
            ),

            zero_cash_companies=(
                "minimum_cash",
                lambda x: (
                    x <= 0
                ).sum()
            ),
        )
    )

    print(
        sector_summary.to_string()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    basic_check(df)

    revenue_analysis(df)

    profitability_analysis(df)

    liquidity_analysis(df)

    credit_analysis(df)

    debt_analysis(df)

    working_capital_analysis(df)

    cash_flow_analysis(df)

    sector_stress_analysis(df)

    size_stress_analysis(df)

    company_distress_analysis(df)

    print("\n" + "=" * 75)

    print(
        "FINANCIAL REALISM VALIDATION COMPLETE"
    )

    print("=" * 75)


if __name__ == "__main__":
    main()