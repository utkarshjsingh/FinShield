import pandas as pd
import numpy as np


# ============================================================
# FINSHIELD FINANCIAL REALISM VALIDATION
# ============================================================

df = pd.read_csv(
    "data/raw/monthly_financials.csv"
)


print("\n" + "="*80)
print("FINSHIELD FINANCIAL REALISM VALIDATION")
print("="*80)


# ============================================================
# BASIC DATA CHECK
# ============================================================

print("\n")
print("="*80)
print("1. BASIC DATA CHECK")
print("="*80)

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Companies:", df["company_id"].nunique())
print("Months:", df["month_index"].nunique())


# ============================================================
# REVENUE ANALYSIS
# ============================================================

print("\n")
print("="*80)
print("2. REVENUE DISTRIBUTION")
print("="*80)


annual_revenue = (
    df.groupby("company_id")
    ["annual_base_revenue"]
    .first()
)


print("\nAnnual revenue:")
print(annual_revenue.describe())


print("\nRevenue by sector:")
print(
    df.groupby("sector")
    ["annual_base_revenue"]
    .mean()
)


print("\nRevenue by size:")
print(
    df.groupby("company_size")
    ["annual_base_revenue"]
    .mean()
)



# ============================================================
# PROFITABILITY
# ============================================================

print("\n")
print("="*80)
print("3. PROFITABILITY")
print("="*80)


df["operating_margin"] = (
    df["operating_profit"]
    /
    df["revenue"]
).replace(
    [np.inf,-np.inf],
    0
)


df["net_margin"] = (
    df["profit_after_tax"]
    /
    df["revenue"]
).replace(
    [np.inf,-np.inf],
    0
)


print("\nOperating margin:")
print(df["operating_margin"].describe())


print("\nNet margin:")
print(df["net_margin"].describe())


print(
    "\nNegative operating profit rows:",
    (df["operating_profit"] < 0).sum()
)



print("\nOperating margin by sector:")
print(
    df.groupby("sector")
    ["operating_margin"]
    .mean()
)



# ============================================================
# LIQUIDITY
# ============================================================

print("\n")
print("="*80)
print("4. LIQUIDITY")
print("="*80)


print(
    "Rows with unfunded deficit:",
    (df["unfunded_deficit"] > 0).sum()
)


print(
    "Total unfunded deficit:",
    df["unfunded_deficit"].sum()
)


print("\nEnding cash:")
print(
    df["ending_cash"].describe()
)



print("\nAvailable liquidity:")
print(
    df["available_liquidity"].describe()
)



# ============================================================
# CREDIT UTILIZATION
# ============================================================

print("\n")
print("="*80)
print("5. CREDIT UTILIZATION")
print("="*80)


credit_util = (
    df["credit_balance"]
    /
    df["credit_limit"]
).fillna(0)


print(
    credit_util.describe()
)


print(
    ">50% utilization:",
    (credit_util > 0.5).mean()*100,
    "%"
)


print(
    ">80% utilization:",
    (credit_util > 0.8).mean()*100,
    "%"
)


print(
    ">95% utilization:",
    (credit_util > 0.95).mean()*100,
    "%"
)



# ============================================================
# DEBT
# ============================================================

print("\n")
print("="*80)
print("6. DEBT BURDEN")
print("="*80)


debt_ratio = (
    df["debt_balance"]
    /
    df["revenue"]
).replace(
    [np.inf,-np.inf],
    0
)


print(
    debt_ratio.describe()
)


print("\nDebt balance:")
print(
    df["debt_balance"].describe()
)



# ============================================================
# WORKING CAPITAL
# ============================================================

print("\n")
print("="*80)
print("7. WORKING CAPITAL")
print("="*80)


for col in [
    "dso",
    "dpo",
    "inventory_days",
    "cash_conversion_cycle"
]:

    print("\n", col)
    print(
        df[col].describe()
    )


print("\nAverage working capital by sector:")

print(
    df.groupby("sector")
    [
        [
            "dso",
            "dpo",
            "inventory_days",
            "cash_conversion_cycle"
        ]
    ]
    .mean()
)



# ============================================================
# CASH FLOW
# ============================================================

print("\n")
print("="*80)
print("8. CASH FLOW")
print("="*80)


print(
    df["net_cash_flow"]
    .describe()
)


print(
    "\nNegative cash-flow rows:",
    (df["net_cash_flow"] < 0).sum()
)



# ============================================================
# COMPANY STRESS
# ============================================================

print("\n")
print("="*80)
print("9. COMPANY LEVEL STRESS")
print("="*80)


company_stress = (
    df.groupby("company_id")
    .agg(
        deficit_months=("unfunded_deficit",
                        lambda x:(x>0).sum()),

        zero_cash_months=("ending_cash",
                          lambda x:(x==0).sum()),

        max_credit=("credit_balance","max"),

        max_revenue=("revenue","max")
    )
)


print(company_stress)


print("\nCompanies with deficits:")
print(
    (company_stress["deficit_months"]>0).sum()
)


print("\nCompanies reaching zero cash:")
print(
    (company_stress["zero_cash_months"]>0).sum()
)



# ============================================================
# FINAL
# ============================================================

print("\n")
print("="*80)
print("FINANCIAL REALISM VALIDATION COMPLETE")
print("="*80)