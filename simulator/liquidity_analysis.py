import pandas as pd
import numpy as np


# ============================================================
# LOAD DATA
# ============================================================

DATA_FILE = "data/raw/monthly_financials.csv"

df = pd.read_csv(DATA_FILE)

print("=" * 70)
print("FINSHIELD - STARTING LIQUIDITY ANALYSIS")
print("=" * 70)

print(f"\nRows: {len(df):,}")
print(f"Companies: {df['company_id'].nunique():,}")


# ============================================================
# GET FIRST MONTH OF EACH COMPANY
# ============================================================

first = (
    df.sort_values(["company_id", "month_index"])
      .groupby("company_id")
      .first()
      .reset_index()
)


# ============================================================
# STARTING CASH VS MONTHLY OUTFLOW
# ============================================================

first["starting_cash_to_outflow"] = (
    first["beginning_cash"]
    / first["total_cash_outflow"].replace(0, np.nan)
)


# ============================================================
# SECTOR ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("STARTING CASH / MONTHLY OUTFLOW BY SECTOR")
print("=" * 70)

sector_ratio = (
    first.groupby("sector")["starting_cash_to_outflow"]
    .agg(["mean", "median", "min", "max"])
    .round(2)
)

print(sector_ratio)


# ============================================================
# STARTING CASH BY SECTOR
# ============================================================

print("\n" + "=" * 70)
print("STARTING CASH BY SECTOR")
print("=" * 70)

sector_cash = (
    first.groupby("sector")["beginning_cash"]
    .agg(["mean", "median", "min", "max"])
    .round(0)
)

print(sector_cash)


# ============================================================
# STARTING CASH BY COMPANY SIZE
# ============================================================

print("\n" + "=" * 70)
print("STARTING CASH / MONTHLY OUTFLOW BY SIZE")
print("=" * 70)

size_ratio = (
    first.groupby("company_size")["starting_cash_to_outflow"]
    .agg(["mean", "median", "min", "max"])
    .round(2)
)

print(size_ratio)


# ============================================================
# DEFICIT RATE BY SECTOR
# ============================================================

print("\n" + "=" * 70)
print("DEFICIT RATE BY SECTOR")
print("=" * 70)

deficit_rate = (
    df.groupby("sector")["unfunded_deficit"]
    .apply(lambda x: (x > 0).mean() * 100)
    .round(2)
)

print(deficit_rate)


# ============================================================
# DEFICIT RATE BY SIZE
# ============================================================

print("\n" + "=" * 70)
print("DEFICIT RATE BY SIZE")
print("=" * 70)

size_deficit = (
    df.groupby("company_size")["unfunded_deficit"]
    .apply(lambda x: (x > 0).mean() * 100)
    .round(2)
)

print(size_deficit)


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS COMPLETED")
print("=" * 70)