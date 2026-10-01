import pandas as pd

# ============================================================
# FINSHIELD COLLECTION EFFICIENCY ANALYSIS
# ============================================================

df = pd.read_csv("data/raw/monthly_financials.csv")
df["month"] = pd.to_datetime(df["month"])

# Collection efficiency:
# How much of the current month's credit sales were collected?
df["collection_efficiency"] = (
    df["collections"] / df["credit_sales"]
).replace([float("inf"), -float("inf")], 0).fillna(0)


print("\n" + "=" * 80)
print("FINSHIELD COLLECTION EFFICIENCY ANALYSIS")
print("=" * 80)


# ============================================================
# 1. DSO SHOCK ROWS
# ============================================================

dso = df[
    df["shock_type"] == "dso_deterioration"
].copy()

print("\nDSO shock rows:", len(dso))
print("Companies affected:", dso["company_id"].nunique())


# ============================================================
# 2. RAW COLLECTION EFFICIENCY
# ============================================================

print("\n" + "=" * 80)
print("1. COLLECTION EFFICIENCY DURING DSO SHOCK")
print("=" * 80)

print(
    dso[
        [
            "company_id",
            "month",
            "shock_severity",
            "dso_shock_multiplier",
            "credit_sales",
            "collections",
            "collection_efficiency",
            "accounts_receivable",
            "dso"
        ]
    ].to_string(index=False)
)


# ============================================================
# 3. BEFORE VS DURING
# ============================================================

print("\n" + "=" * 80)
print("2. BEFORE VS DURING")
print("=" * 80)

results = []

for company in dso["company_id"].unique():

    company_df = (
        df[df["company_id"] == company]
        .sort_values("month")
    )

    shock = company_df[
        company_df["shock_type"] == "dso_deterioration"
    ]

    start = shock["month"].min()
    end = shock["month"].max()

    before = company_df[
        (company_df["month"] < start)
        &
        (
            company_df["month"]
            >= start - pd.DateOffset(months=3)
        )
    ]

    during = company_df[
        (company_df["month"] >= start)
        &
        (company_df["month"] <= end)
    ]

    results.append({
        "company_id": company,

        "before_efficiency":
            before["collection_efficiency"].mean(),

        "during_efficiency":
            during["collection_efficiency"].mean(),

        "before_ar":
            before["accounts_receivable"].mean(),

        "during_ar":
            during["accounts_receivable"].mean(),

        "before_dso":
            before["dso"].mean(),

        "during_dso":
            during["dso"].mean(),

        "before_cashflow":
            before["net_cash_flow"].mean(),

        "during_cashflow":
            during["net_cash_flow"].mean()
    })


result = pd.DataFrame(results)

result["efficiency_change"] = (
    result["during_efficiency"]
    - result["before_efficiency"]
)

result["ar_change"] = (
    result["during_ar"]
    - result["before_ar"]
)

result["dso_change"] = (
    result["during_dso"]
    - result["before_dso"]
)

result["cashflow_change"] = (
    result["during_cashflow"]
    - result["before_cashflow"]
)


# ============================================================
# 4. OVERALL RESULTS
# ============================================================

print("\n" + "=" * 80)
print("3. OVERALL COLLECTION EFFICIENCY")
print("=" * 80)

before_eff = result["before_efficiency"].mean()
during_eff = result["during_efficiency"].mean()

print(f"Before shock: {before_eff:.4f}")
print(f"During shock: {during_eff:.4f}")
print(f"Change:       {during_eff - before_eff:.4f}")

print("\nAs percentages:")

print(
    f"Before: {before_eff * 100:.2f}%"
)

print(
    f"During: {during_eff * 100:.2f}%"
)

print(
    f"Change: {(during_eff - before_eff) * 100:.2f} percentage points"
)


# ============================================================
# 5. AR / DSO / CASH FLOW
# ============================================================

print("\n" + "=" * 80)
print("4. AR / DSO / CASH FLOW")
print("=" * 80)

for metric in [
    "ar",
    "dso",
    "cashflow"
]:

    before = result[f"before_{metric}"].mean()
    during = result[f"during_{metric}"].mean()

    print(
        f"{metric:15s}"
        f" Before: {before:,.2f}"
        f" | During: {during:,.2f}"
        f" | Change: {during - before:,.2f}"
    )


# ============================================================
# 6. COMPANY LEVEL
# ============================================================

print("\n" + "=" * 80)
print("5. COMPANY-LEVEL RESULTS")
print("=" * 80)

print(
    result[
        [
            "company_id",
            "efficiency_change",
            "ar_change",
            "dso_change",
            "cashflow_change"
        ]
    ]
    .sort_values("efficiency_change")
    .to_string(index=False)
)


# ============================================================
# 7. DIAGNOSTIC
# ============================================================

print("\n" + "=" * 80)
print("6. QUICK DIAGNOSTIC")
print("=" * 80)

total = len(result)

efficiency_down = (
    result["efficiency_change"] < 0
).sum()

ar_up = (
    result["ar_change"] > 0
).sum()

dso_up = (
    result["dso_change"] > 0
).sum()

cashflow_down = (
    result["cashflow_change"] < 0
).sum()

print(
    f"Collection efficiency decreased: "
    f"{efficiency_down}/{total}"
)

print(
    f"AR increased: "
    f"{ar_up}/{total}"
)

print(
    f"DSO increased: "
    f"{dso_up}/{total}"
)

print(
    f"Cash flow deteriorated: "
    f"{cashflow_down}/{total}"
)


print("\n" + "=" * 80)
print("COLLECTION EFFICIENCY ANALYSIS COMPLETE")
print("=" * 80)