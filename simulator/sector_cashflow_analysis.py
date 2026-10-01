import pandas as pd
import numpy as np

DATA_FILE = "data/raw/monthly_financials.csv"

df = pd.read_csv(DATA_FILE)

print("=" * 70)
print("FINSHIELD - SECTOR CASH FLOW ANALYSIS")
print("=" * 70)

# Create credit utilization because it is not stored
# directly in monthly_financials.csv
df["credit_utilization"] = (
    df["credit_balance"]
    / df["credit_limit"].replace(0, np.nan)
)


# ============================================================
# PROFITABILITY
# ============================================================

print("\n" + "=" * 70)
print("PROFITABILITY BY SECTOR")
print("=" * 70)

df["operating_margin"] = (
    df["operating_profit"]
    / df["revenue"].replace(0, np.nan)
)

profitability = (
    df.groupby("sector")
      .agg(
          avg_revenue=("revenue", "mean"),
          avg_operating_profit=("operating_profit", "mean"),
          operating_margin=("operating_margin", "mean"),
          negative_profit_rate=(
              "operating_profit",
              lambda x: (x < 0).mean() * 100
          )
      )
      .round(3)
)

print(profitability)


# ============================================================
# CASH FLOW
# ============================================================

print("\n" + "=" * 70)
print("CASH FLOW BY SECTOR")
print("=" * 70)

cashflow = (
    df.groupby("sector")
      .agg(
          avg_net_cash_flow=("net_cash_flow", "mean"),
          negative_cashflow_rate=(
              "net_cash_flow",
              lambda x: (x < 0).mean() * 100
          ),
          avg_ending_cash=("ending_cash", "mean"),
          avg_available_liquidity=("available_liquidity", "mean"),
          avg_credit_utilization=(
              "credit_utilization",
              "mean"
          )
      )
      .round(3)
)

print(cashflow)


# ============================================================
# WORKING CAPITAL
# ============================================================

print("\n" + "=" * 70)
print("WORKING CAPITAL BY SECTOR")
print("=" * 70)

working_capital = (
    df.groupby("sector")
      .agg(
          dso=("dso", "mean"),
          inventory_days=("inventory_days", "mean"),
          dpo=("dpo", "mean"),
          ccc=("cash_conversion_cycle", "mean")
      )
      .round(2)
)

print(working_capital)


# ============================================================
# DEBT
# ============================================================

print("\n" + "=" * 70)
print("DEBT BY SECTOR")
print("=" * 70)

debt = (
    df.groupby("sector")
      .agg(
          avg_debt=("debt_balance", "mean"),
          avg_loan_payment=("loan_payment", "mean"),
          avg_credit_utilization=(
              "credit_utilization",
              "mean"
          )
      )
      .round(2)
)

print(debt)


# ============================================================
# LIQUIDITY STRESS
# ============================================================

print("\n" + "=" * 70)
print("LIQUIDITY STRESS BY SECTOR")
print("=" * 70)

stress = (
    df.groupby("sector")
      .agg(
          deficit_rate=(
              "unfunded_deficit",
              lambda x: (x > 0).mean() * 100
          ),
          avg_deficit=(
              "unfunded_deficit",
              lambda x: (
                  x[x > 0].mean()
                  if (x > 0).any()
                  else 0
              )
          )
      )
      .round(2)
)

print(stress)


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS COMPLETED")
print("=" * 70)