import pandas as pd

# ============================================================
# FINSHIELD SHOCK IMPACT ANALYSIS
# ============================================================

# Load simulated dataset
df = pd.read_csv("data/raw/monthly_financials.csv")


print("\n" + "=" * 70)
print("FINSHIELD SHOCK IMPACT ANALYSIS")
print("=" * 70)


# ============================================================
# 1. BASIC CHECKS
# ============================================================

print("\n1. BASIC CHECKS")
print("-" * 70)

print("Shape:", df.shape)
print("Companies:", df["company_id"].nunique())

print("\nMonths per company:")
print(df.groupby("company_id").size().value_counts())


# ============================================================
# 2. CALCULATE DERIVED METRICS
# ============================================================

# Cash Conversion Cycle
df["ccc"] = (
    df["dso"]
    + df["inventory_days"]
    - df["dpo"]
)

# Credit utilization
df["credit_utilization"] = (
    df["credit_balance"] / df["credit_limit"]
).fillna(0)


# ============================================================
# 3. SHOCK COVERAGE
# ============================================================

print("\n2. SHOCK COVERAGE")
print("-" * 70)

print("\nShock active:")
print(df["shock_active"].value_counts())

print("\nShock types:")

shock_rows = df[df["shock_active"] == True]

if len(shock_rows) > 0:
    print(shock_rows["shock_type"].value_counts())
else:
    print("No shock rows found.")


# ============================================================
# 4. SHOCK VS NON-SHOCK
# ============================================================

cols = [
    "revenue",
    "dso",
    "inventory_days",
    "dpo",
    "ccc",
    "net_cash_flow",
    "ending_cash",
    "credit_utilization",
    "unfunded_deficit"
]

print("\n3. SHOCK VS NON-SHOCK")
print("-" * 70)

print(
    df.groupby("shock_active")[cols]
    .mean()
    .round(2)
)


# ============================================================
# 5. DEFICITS BY SHOCK STATE
# ============================================================

print("\n4. DEFICITS BY SHOCK STATE")
print("-" * 70)

print(
    df.groupby("shock_active")["unfunded_deficit"]
    .agg([
        "count",
        "sum",
        "mean",
        "max"
    ])
    .round(2)
)


# ============================================================
# 6. DEFICITS BY SHOCK TYPE
# ============================================================

print("\n5. DEFICITS BY SHOCK TYPE")
print("-" * 70)

print(
    df.groupby("shock_type")["unfunded_deficit"]
    .agg([
        "count",
        "sum",
        "mean",
        "max"
    ])
    .sort_values("sum", ascending=False)
    .round(2)
)


# ============================================================
# 7. FINANCIAL METRICS BY SHOCK TYPE
# ============================================================

print("\n6. FINANCIAL METRICS BY SHOCK TYPE")
print("-" * 70)

print(
    df.groupby("shock_type")[
        [
            "revenue",
            "dso",
            "inventory_days",
            "dpo",
            "ccc",
            "net_cash_flow",
            "ending_cash",
            "credit_utilization"
        ]
    ]
    .mean()
    .round(2)
)


# ============================================================
# 8. SHOCK MULTIPLIERS
# ============================================================

print("\n7. SHOCK MULTIPLIERS")
print("-" * 70)

multiplier_cols = [
    "revenue_shock_multiplier",
    "dso_shock_multiplier",
    "inventory_shock_multiplier",
    "cogs_shock_multiplier",
    "dpo_shock_multiplier",
    "expense_shock_multiplier"
]

print(
    df[df["shock_active"] == True][
        multiplier_cols
    ]
    .describe()
    .round(3)
)


# ============================================================
# 9. WORST SHOCK MONTHS
# ============================================================

print("\n8. WORST SHOCK MONTHS BY UNFUNDED DEFICIT")
print("-" * 70)

worst = (
    df[df["shock_active"] == True]
    .sort_values("unfunded_deficit", ascending=False)
    [
        [
            "company_id",
            "month",
            "shock_type",
            "shock_severity",
            "revenue",
            "dso",
            "inventory_days",
            "dpo",
            "ccc",
            "ending_cash",
            "credit_utilization",
            "unfunded_deficit"
        ]
    ]
    .head(15)
)

print(worst.to_string(index=False))


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print("\nDataset:")
print(f"  Companies: {df['company_id'].nunique()}")
print(f"  Rows: {len(df):,}")

print("\nShock months:")
print(f"  {df['shock_active'].sum():,}")

print("\nNon-shock months:")
print(f"  {(~df['shock_active']).sum():,}")

print("\nDeficit rows:")
print(f"  {(df['unfunded_deficit'] > 0).sum():,}")

print("\n" + "=" * 70)


