import pandas as pd

# ============================================================
# FINSHIELD DSO SHOCK DEEP-DIVE
# ============================================================

df = pd.read_csv("data/raw/monthly_financials.csv")
df["month"] = pd.to_datetime(df["month"])

# ------------------------------------------------------------
# Calculate credit utilization if not already present
# ------------------------------------------------------------

if "credit_utilization" not in df.columns:
    df["credit_utilization"] = (
        df["credit_balance"] / df["credit_limit"]
    ).fillna(0)


# ------------------------------------------------------------
# Find DSO shock rows
# ------------------------------------------------------------

dso = df[
    df["shock_type"] == "dso_deterioration"
].copy()


print("\n" + "=" * 80)
print("FINSHIELD DSO SHOCK DEEP-DIVE")
print("=" * 80)

print("\nDSO shock rows:", len(dso))
print("Companies affected:", dso["company_id"].nunique())


# ============================================================
# 1. DSO SHOCK MULTIPLIER
# ============================================================

print("\n" + "=" * 80)
print("1. DSO SHOCK MULTIPLIER")
print("=" * 80)

print(
    dso[
        [
            "company_id",
            "month",
            "shock_severity",
            "dso_shock_multiplier",
            "dso"
        ]
    ].to_string(index=False)
)


# ============================================================
# 2. CHECK AVAILABLE WORKING-CAPITAL COLUMNS
# ============================================================

print("\n" + "=" * 80)
print("2. AVAILABLE WORKING-CAPITAL COLUMNS")
print("=" * 80)

possible_columns = [
    "revenue",
    "credit_sales",
    "collections",
    "accounts_receivable",
    "ar",
    "dso",
    "net_cash_flow",
    "ending_cash",
    "credit_balance",
    "credit_limit",
    "credit_utilization",
    "unfunded_deficit"
]

available = [
    col for col in possible_columns
    if col in df.columns
]

missing = [
    col for col in possible_columns
    if col not in df.columns
]

print("\nAvailable:")
print(available)

print("\nNot available:")
print(missing)


# ============================================================
# 3. RAW DSO SHOCK ROWS
# ============================================================

print("\n" + "=" * 80)
print("3. RAW DSO SHOCK ROWS")
print("=" * 80)

display_columns = [
    col for col in [
        "company_id",
        "month",
        "shock_severity",
        "dso_shock_multiplier",
        "revenue",
        "credit_sales",
        "collections",
        "accounts_receivable",
        "ar",
        "dso",
        "net_cash_flow",
        "ending_cash",
        "credit_balance",
        "credit_utilization",
        "unfunded_deficit"
    ]
    if col in df.columns
]

print(
    dso[display_columns]
    .to_string(index=False)
)


# ============================================================
# 4. BEFORE VS DURING
# ============================================================

print("\n" + "=" * 80)
print("4. BEFORE VS DURING DSO SHOCK")
print("=" * 80)

metrics = [
    col for col in [
        "revenue",
        "credit_sales",
        "collections",
        "accounts_receivable",
        "ar",
        "dso",
        "net_cash_flow",
        "ending_cash",
        "credit_balance",
        "credit_utilization",
        "unfunded_deficit"
    ]
    if col in df.columns
]

results = []

for company in dso["company_id"].unique():

    company_df = (
        df[df["company_id"] == company]
        .sort_values("month")
    )

    shock_months = company_df[
        company_df["shock_type"] == "dso_deterioration"
    ]

    start = shock_months["month"].min()
    end = shock_months["month"].max()

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

    result = {
        "company_id": company,
        "start": start,
        "end": end
    }

    for metric in metrics:

        result[f"before_{metric}"] = before[metric].mean()
        result[f"during_{metric}"] = during[metric].mean()

    results.append(result)


result_df = pd.DataFrame(results)


# ============================================================
# 5. OVERALL COMPARISON
# ============================================================

print("\n" + "=" * 80)
print("5. OVERALL BEFORE VS DURING")
print("=" * 80)

for metric in metrics:

    before = result_df[
        f"before_{metric}"
    ].mean()

    during = result_df[
        f"during_{metric}"
    ].mean()

    change = during - before

    print(
        f"{metric:25s}"
        f" Before: {before:,.2f}"
        f" | During: {during:,.2f}"
        f" | Change: {change:,.2f}"
    )


# ============================================================
# 6. COMPANY-LEVEL DSO CHANGE
# ============================================================

print("\n" + "=" * 80)
print("6. COMPANY-LEVEL DSO CHANGE")
print("=" * 80)

result_df["dso_change"] = (
    result_df["during_dso"]
    - result_df["before_dso"]
)

if "accounts_receivable" in df.columns:

    result_df["ar_change"] = (
        result_df["during_accounts_receivable"]
        - result_df["before_accounts_receivable"]
    )

elif "ar" in df.columns:

    result_df["ar_change"] = (
        result_df["during_ar"]
        - result_df["before_ar"]
    )

if "collections" in df.columns:

    result_df["collection_change"] = (
        result_df["during_collections"]
        - result_df["before_collections"]
    )

result_df["cashflow_change"] = (
    result_df["during_net_cash_flow"]
    - result_df["before_net_cash_flow"]
)


company_display = [
    "company_id",
    "dso_change"
]

if "ar_change" in result_df.columns:
    company_display.append("ar_change")

if "collection_change" in result_df.columns:
    company_display.append("collection_change")

company_display.append("cashflow_change")

print(
    result_df[
        company_display
    ]
    .sort_values("dso_change", ascending=False)
    .to_string(index=False)
)


# ============================================================
# 7. QUICK DIAGNOSTIC
# ============================================================

print("\n" + "=" * 80)
print("7. QUICK DIAGNOSTIC")
print("=" * 80)

total = len(result_df)

positive_dso = (
    result_df["dso_change"] > 0
).sum()

print(
    f"Companies where DSO increased: "
    f"{positive_dso}/{total}"
)

print(
    f"Percentage with increased DSO: "
    f"{positive_dso / total * 100:.1f}%"
)

if "ar_change" in result_df.columns:

    positive_ar = (
        result_df["ar_change"] > 0
    ).sum()

    print(
        f"Companies where AR increased: "
        f"{positive_ar}/{total}"
    )

negative_cashflow = (
    result_df["cashflow_change"] < 0
).sum()

print(
    f"Companies where cash flow deteriorated: "
    f"{negative_cashflow}/{total}"
)


print("\n" + "=" * 80)
print("DSO DEEP-DIVE COMPLETE")
print("=" * 80)