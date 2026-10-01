import pandas as pd
import numpy as np

# ============================================================
# FINSHIELD SHOCK EVENT ANALYSIS
# Compare each company's financial condition before vs during
# its own shock event.
# ============================================================

df = pd.read_csv("data/raw/monthly_financials.csv")

df["month"] = pd.to_datetime(df["month"])

# Derived metrics
df["ccc"] = (
    df["dso"]
    + df["inventory_days"]
    - df["dpo"]
)

df["credit_utilization"] = (
    df["credit_balance"] / df["credit_limit"]
).fillna(0)


# ============================================================
# 1. CREATE SHOCK EVENT IDs
# ============================================================

df = df.sort_values(["company_id", "month"]).reset_index(drop=True)

# A new event starts when:
# - shock becomes active after being inactive
# - OR shock type changes

df["previous_shock_active"] = (
    df.groupby("company_id")["shock_active"]
    .shift(1)
    .fillna(False)
)

df["new_event"] = (
    (df["shock_active"] == True)
    &
    (
        (df["previous_shock_active"] == False)
        |
        (
            df.groupby("company_id")["shock_type"]
            .shift(1)
            != df["shock_type"]
        )
    )
)

df["event_number"] = (
    df.groupby("company_id")["new_event"]
    .cumsum()
)

df["event_id"] = np.where(
    df["shock_active"],
    df["company_id"] + "_EVENT_" + df["event_number"].astype(str),
    None
)


# ============================================================
# 2. FIND SHOCK EVENTS
# ============================================================

events = (
    df[df["shock_active"]]
    .groupby("event_id")
    .agg(
        company_id=("company_id", "first"),
        shock_type=("shock_type", "first"),
        shock_severity=("shock_severity", "first"),
        start_date=("month", "min"),
        end_date=("month", "max"),
        shock_months=("month", "count")
    )
    .reset_index()
)

print("\n" + "=" * 80)
print("FINSHIELD SHOCK EVENT ANALYSIS")
print("=" * 80)

print("\nTotal shock events:", len(events))

print("\nEvents by shock type:")
print(events["shock_type"].value_counts())


# ============================================================
# 3. CREATE BEFORE / DURING / AFTER WINDOWS
# ============================================================

metrics = [
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

results = []

for _, event in events.iterrows():

    company = event["company_id"]
    start = event["start_date"]
    end = event["end_date"]

    company_df = df[df["company_id"] == company].copy()

    # 3 months before shock
    before = company_df[
        (company_df["month"] < start)
        &
        (company_df["month"] >= start - pd.DateOffset(months=3))
    ]

    # During shock
    during = company_df[
        (company_df["month"] >= start)
        &
        (company_df["month"] <= end)
    ]

    # 3 months after shock
    after = company_df[
        (company_df["month"] > end)
        &
        (company_df["month"] <= end + pd.DateOffset(months=3))
    ]

    result = {
        "event_id": event["event_id"],
        "company_id": company,
        "shock_type": event["shock_type"],
        "severity": event["shock_severity"],
        "start": start,
        "end": end
    }

    for metric in metrics:

        result[f"before_{metric}"] = before[metric].mean()
        result[f"during_{metric}"] = during[metric].mean()
        result[f"after_{metric}"] = after[metric].mean()

    results.append(result)


event_df = pd.DataFrame(results)


# ============================================================
# 4. CHANGE FROM BEFORE → DURING
# ============================================================

for metric in metrics:

    event_df[f"change_{metric}"] = (
        event_df[f"during_{metric}"]
        - event_df[f"before_{metric}"]
    )


# ============================================================
# 5. OVERALL EVENT IMPACT
# ============================================================

print("\n" + "=" * 80)
print("OVERALL BEFORE vs DURING SHOCK")
print("=" * 80)

for metric in metrics:

    before_mean = event_df[f"before_{metric}"].mean()
    during_mean = event_df[f"during_{metric}"].mean()

    change = during_mean - before_mean

    print(
        f"{metric:25s} "
        f"Before: {before_mean:,.2f}   "
        f"During: {during_mean:,.2f}   "
        f"Change: {change:,.2f}"
    )


# ============================================================
# 6. IMPACT BY SHOCK TYPE
# ============================================================

print("\n" + "=" * 80)
print("IMPACT BY SHOCK TYPE")
print("=" * 80)

for shock_type in sorted(event_df["shock_type"].unique()):

    subset = event_df[
        event_df["shock_type"] == shock_type
    ]

    print("\n" + "-" * 80)
    print(shock_type)
    print("Events:", len(subset))
    print("-" * 80)

    for metric in [
        "revenue",
        "dso",
        "inventory_days",
        "dpo",
        "ccc",
        "net_cash_flow",
        "ending_cash",
        "credit_utilization",
        "unfunded_deficit"
    ]:

        before = subset[f"before_{metric}"].mean()
        during = subset[f"during_{metric}"].mean()
        change = during - before

        print(
            f"{metric:25s} "
            f"Before: {before:,.2f}   "
            f"During: {during:,.2f}   "
            f"Change: {change:,.2f}"
        )


# ============================================================
# 7. SHOCKS THAT CAUSED DEFICITS
# ============================================================

print("\n" + "=" * 80)
print("SHOCK EVENTS WITH UNFUNDED DEFICITS")
print("=" * 80)

deficit_events = event_df[
    event_df["during_unfunded_deficit"] > 0
]

print(
    "Events with deficit:",
    len(deficit_events),
    "/",
    len(event_df)
)

if len(deficit_events) > 0:

    print("\nBy shock type:")
    print(
        deficit_events["shock_type"]
        .value_counts()
    )


# ============================================================
# 8. SHOW INDIVIDUAL EVENTS
# ============================================================

print("\n" + "=" * 80)
print("SAMPLE EVENT RESULTS")
print("=" * 80)

display_cols = [
    "event_id",
    "company_id",
    "shock_type",
    "severity",
    "start",
    "end",
    "before_revenue",
    "during_revenue",
    "before_dso",
    "during_dso",
    "before_inventory_days",
    "during_inventory_days",
    "before_ccc",
    "during_ccc",
    "before_net_cash_flow",
    "during_net_cash_flow",
    "before_credit_utilization",
    "during_credit_utilization",
    "during_unfunded_deficit"
]

print(
    event_df[display_cols]
    .head(20)
    .to_string(index=False)
)


print("\n" + "=" * 80)
print("EVENT ANALYSIS COMPLETE")
print("=" * 80)