"""
FinShield - Ground Truth Engine

Creates:
    current_score / current_label
    target_1m_score / target_1m_label
    target_2m_score / target_2m_label
    target_3m_score / target_3m_label

The original simulation dataset is NOT modified.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/raw/monthly_financials.csv")

OUTPUT_DIR = Path("data/model_ready")
OUTPUT_FILE = OUTPUT_DIR / "ground_truth_dataset.csv"

MIN_CASH_MULTIPLIER = 1.0

GOOD_THRESHOLD = 70
WATCH_THRESHOLD = 40


# ============================================================
# BASIC HELPERS
# ============================================================

def clip_score(value):
    """Keep health score between 0 and 100."""
    return np.clip(value, 0, 100)


def score_from_ratio(
    ratio,
    good_ratio=2.0,
    zero_ratio=0.0,
):
    """
    Convert a financial ratio into a 0-100 score.

    ratio >= good_ratio -> 100
    ratio <= zero_ratio -> 0
    """

    ratio = np.asarray(ratio, dtype=float)

    denominator = good_ratio - zero_ratio

    score = (
        (ratio - zero_ratio)
        / denominator
        * 100
    )

    return clip_score(score)


def label_from_score(score):
    """Convert a score into Good / Watch / Critical."""

    if score >= GOOD_THRESHOLD:
        return "Good"

    if score >= WATCH_THRESHOLD:
        return "Watch"

    return "Critical"


def labels_from_scores(scores):
    """
    Vectorized version of label_from_score().
    """

    scores = np.asarray(scores, dtype=float)

    labels = np.full(
        scores.shape,
        None,
        dtype=object,
    )

    valid = ~np.isnan(scores)

    labels[
        valid & (scores >= GOOD_THRESHOLD)
    ] = "Good"

    labels[
        valid
        & (scores >= WATCH_THRESHOLD)
        & (scores < GOOD_THRESHOLD)
    ] = "Watch"

    labels[
        valid & (scores < WATCH_THRESHOLD)
    ] = "Critical"

    return labels


# ============================================================
# WORKING CAPITAL SCORE
# ============================================================

def working_capital_score(
    dso,
    inventory_days,
    dpo,
    ccc,
):
    """
    Calculate working-capital health score.

    Lower DSO, inventory days and CCC are generally healthier.

    Higher DPO provides supplier financing, but is capped so
    extremely high DPO does not receive unlimited benefit.
    """

    dso = np.asarray(dso, dtype=float)
    inventory_days = np.asarray(
        inventory_days,
        dtype=float,
    )
    dpo = np.asarray(dpo, dtype=float)
    ccc = np.asarray(ccc, dtype=float)

    dso_score = (
        100
        - np.clip(
            (dso / 120) * 100,
            0,
            100,
        )
    )

    inventory_score = (
        100
        - np.clip(
            (inventory_days / 120) * 100,
            0,
            100,
        )
    )

    dpo_score = np.clip(
        (dpo / 120) * 100,
        0,
        100,
    )

    ccc_score = (
        100
        - np.clip(
            (ccc / 120) * 100,
            0,
            100,
        )
    )

    score = (
        0.30 * dso_score
        + 0.25 * inventory_score
        + 0.20 * dpo_score
        + 0.25 * ccc_score
    )

    return clip_score(score)


# ============================================================
# DEBT SERVICE SCORE
# ============================================================

def debt_service_score(
    operating_cash_flow,
    loan_payment,
):
    """
    Approximate debt-service health using:

        DSCR = operating cash flow / loan payment

    DSCR <= 0   -> 0
    DSCR = 1    -> 50
    DSCR >= 2   -> 100
    """

    operating_cash_flow = np.asarray(
        operating_cash_flow,
        dtype=float,
    )

    loan_payment = np.asarray(
        loan_payment,
        dtype=float,
    )

    dscr = np.divide(
        operating_cash_flow,
        loan_payment,
        out=np.full_like(
            operating_cash_flow,
            2.0,
            dtype=float,
        ),
        where=loan_payment > 0,
    )

    score = np.clip(
        dscr / 2.0 * 100,
        0,
        100,
    )

    return score


# ============================================================
# STABILITY SCORE
# ============================================================

def stability_score(
    cash_flows,
):
    """
    Calculate cash-flow stability score.

    Lower volatility relative to cash-flow magnitude
    receives a higher score.
    """

    values = np.asarray(
        cash_flows,
        dtype=float,
    )

    if len(values) <= 1:
        return 50.0

    mean_abs = np.mean(
        np.abs(values)
    )

    if mean_abs <= 1e-9:
        return 50.0

    volatility = (
        np.std(values)
        / mean_abs
    )

    score = (
        100
        - np.clip(
            volatility * 100,
            0,
            100,
        )
    )

    return float(score)


# ============================================================
# CURRENT HEALTH SCORE - VECTORIZED
# ============================================================

def calculate_current_scores(df):
    """
    Calculate current health score for every row.

    This version is vectorized for speed.
    """

    minimum_cash = (
        df["total_cash_outflow"]
        .clip(lower=1.0)
        * MIN_CASH_MULTIPLIER
    )

    # --------------------------------------------------------
    # 1. Liquidity resilience
    # --------------------------------------------------------

    liquidity_ratio = (
        df["available_liquidity"]
        / minimum_cash
    )

    liquidity_score = score_from_ratio(
        liquidity_ratio,
        good_ratio=2.0,
    )

    # --------------------------------------------------------
    # 2. Current cash stress
    # --------------------------------------------------------

    cash_ratio = (
        df["ending_cash"]
        / minimum_cash
    )

    cash_stress_score = score_from_ratio(
        cash_ratio,
        good_ratio=2.0,
    )

    deficit_mask = (
        df["unfunded_deficit"]
        > 0
    )

    cash_stress_score[
        deficit_mask.to_numpy()
    ] = 0.0

    # --------------------------------------------------------
    # 3. Working capital
    # --------------------------------------------------------

    wc_score = working_capital_score(
        df["dso"].to_numpy(),
        df["inventory_days"].to_numpy(),
        df["dpo"].to_numpy(),
        df["cash_conversion_cycle"].to_numpy(),
    )

    # --------------------------------------------------------
    # 4. Debt service
    # --------------------------------------------------------

    operating_cash_flow = (
        df["operating_inflows"]
        - df["total_cash_outflow"]
    )

    debt_score = debt_service_score(
        operating_cash_flow.to_numpy(),
        df["loan_payment"].to_numpy(),
    )

    # --------------------------------------------------------
    # 5. Stability
    #
    # Current-row ground truth does not have enough information
    # to calculate historical volatility here.
    #
    # Therefore use the configured neutral baseline.
    # --------------------------------------------------------

    stability = np.full(
        len(df),
        50.0,
    )

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    score = (
        0.30 * liquidity_score
        + 0.30 * cash_stress_score
        + 0.15 * wc_score
        + 0.15 * debt_score
        + 0.10 * stability
    )

    # Safety override
    score[
        deficit_mask.to_numpy()
    ] = np.minimum(
        score[
            deficit_mask.to_numpy()
        ],
        39.0,
    )

    return clip_score(score)


# ============================================================
# PREPARE NUMPY MATRICES
# ============================================================

def make_matrix(
    df,
    column,
    companies,
    months,
):
    """
    Convert a dataframe column into:

        companies × months

    matrix.
    """

    return (
        df[column]
        .to_numpy(dtype=float)
        .reshape(
            companies,
            months,
        )
    )


# ============================================================
# FUTURE TARGET CALCULATION
# ============================================================

def calculate_future_targets(
    df,
    horizon,
):
    """
    Calculate future health score for a given horizon.

    horizon = 1:
        use next 1 month

    horizon = 2:
        use next 2 months

    horizon = 3:
        use next 3 months

    This uses complete simulated future information
    intentionally because this is ground truth generation.
    """

    companies = (
        df["company_id"]
        .nunique()
    )

    months = (
        df.groupby("company_id")
        .size()
        .iloc[0]
    )

    # --------------------------------------------------------
    # Create matrices
    # --------------------------------------------------------

    available_liquidity = make_matrix(
        df,
        "available_liquidity",
        companies,
        months,
    )

    ending_cash = make_matrix(
        df,
        "ending_cash",
        companies,
        months,
    )

    unfunded_deficit = make_matrix(
        df,
        "unfunded_deficit",
        companies,
        months,
    )

    dso = make_matrix(
        df,
        "dso",
        companies,
        months,
    )

    inventory_days = make_matrix(
        df,
        "inventory_days",
        companies,
        months,
    )

    dpo = make_matrix(
        df,
        "dpo",
        companies,
        months,
    )

    ccc = make_matrix(
        df,
        "cash_conversion_cycle",
        companies,
        months,
    )

    total_cash_outflow = make_matrix(
        df,
        "total_cash_outflow",
        companies,
        months,
    )

    operating_inflows = make_matrix(
        df,
        "operating_inflows",
        companies,
        months,
    )

    loan_payment = make_matrix(
        df,
        "loan_payment",
        companies,
        months,
    )

    operating_cash_flow = (
        operating_inflows
        - total_cash_outflow
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    scores = np.full(
        (companies, months),
        np.nan,
        dtype=float,
    )

    # --------------------------------------------------------
    # Calculate each prediction month
    #
    # This loops over only 36 month positions,
    # not over 360,000 dataframe rows.
    # --------------------------------------------------------

    for t in range(
        months - horizon
    ):

        start = t + 1
        end = t + 1 + horizon

        # Future windows
        future_liquidity = (
            available_liquidity[
                :,
                start:end,
            ]
        )

        future_cash = (
            ending_cash[
                :,
                start:end,
            ]
        )

        future_deficit = (
            unfunded_deficit[
                :,
                start:end,
            ]
        )

        future_dso = (
            dso[
                :,
                start:end,
            ]
        )

        future_inventory = (
            inventory_days[
                :,
                start:end,
            ]
        )

        future_dpo = (
            dpo[
                :,
                start:end,
            ]
        )

        future_ccc = (
            ccc[
                :,
                start:end,
            ]
        )

        future_outflow = (
            total_cash_outflow[
                :,
                start:end,
            ]
        )

        future_ocf = (
            operating_cash_flow[
                :,
                start:end,
            ]
        )

        future_payment = (
            loan_payment[
                :,
                start:end,
            ]
        )

        # ----------------------------------------------------
        # Minimum cash requirement
        # ----------------------------------------------------

        avg_outflow = np.maximum(
            np.mean(
                future_outflow,
                axis=1,
            ),
            1.0,
        )

        minimum_cash = (
            avg_outflow
            * MIN_CASH_MULTIPLIER
        )

        # ----------------------------------------------------
        # Liquidity resilience
        # ----------------------------------------------------

        minimum_liquidity = np.min(
            future_liquidity,
            axis=1,
        )

        liquidity_ratio = (
            minimum_liquidity
            / minimum_cash
        )

        liquidity_score = score_from_ratio(
            liquidity_ratio,
            good_ratio=2.0,
        )

        # ----------------------------------------------------
        # Future cash stress
        # ----------------------------------------------------

        minimum_cash_balance = np.min(
            future_cash,
            axis=1,
        )

        cash_ratio = (
            minimum_cash_balance
            / minimum_cash
        )

        cash_stress_score = score_from_ratio(
            cash_ratio,
            good_ratio=2.0,
        )

        # ----------------------------------------------------
        # Deficit override
        # ----------------------------------------------------

        maximum_deficit = np.max(
            future_deficit,
            axis=1,
        )

        deficit_mask = (
            maximum_deficit > 0
        )

        cash_stress_score[
            deficit_mask
        ] = 0.0

        # ----------------------------------------------------
        # Working capital
        # ----------------------------------------------------

        wc_score = working_capital_score(
            np.mean(
                future_dso,
                axis=1,
            ),
            np.mean(
                future_inventory,
                axis=1,
            ),
            np.mean(
                future_dpo,
                axis=1,
            ),
            np.mean(
                future_ccc,
                axis=1,
            ),
        )

        # ----------------------------------------------------
        # Debt service
        # ----------------------------------------------------

        avg_ocf = np.mean(
            future_ocf,
            axis=1,
        )

        avg_payment = np.mean(
            future_payment,
            axis=1,
        )

        debt_score = debt_service_score(
            avg_ocf,
            avg_payment,
        )

        # ----------------------------------------------------
        # Cash-flow stability
        # ----------------------------------------------------

        mean_abs = np.mean(
            np.abs(future_ocf),
            axis=1,
        )

        std_ocf = np.std(
            future_ocf,
            axis=1,
        )

        volatility = np.divide(
            std_ocf,
            mean_abs,
            out=np.zeros_like(
                std_ocf
            ),
            where=mean_abs > 1e-9,
        )

        stability = (
            100
            - np.clip(
                volatility * 100,
                0,
                100,
            )
        )

        # ----------------------------------------------------
        # Final weighted score
        # ----------------------------------------------------

        score = (
            0.30 * liquidity_score
            + 0.30 * cash_stress_score
            + 0.15 * wc_score
            + 0.15 * debt_score
            + 0.10 * stability
        )

        # Safety override
        score[
            deficit_mask
        ] = np.minimum(
            score[
                deficit_mask
            ],
            39.0,
        )

        scores[
            :,
            t
        ] = clip_score(score)

    return scores


# ============================================================
# CREATE COMPLETE GROUND TRUTH DATASET
# ============================================================

def create_ground_truth(df):

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = (
        df.sort_values(
            [
                "company_id",
                "month_index",
            ]
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Verify structure
    # --------------------------------------------------------

    company_counts = (
        df.groupby("company_id")
        .size()
    )

    if company_counts.nunique() != 1:
        raise ValueError(
            "Companies do not have equal month counts."
        )

    companies = (
        df["company_id"]
        .nunique()
    )

    months = (
        company_counts.iloc[0]
    )

    print(
        f"\nCompanies: {companies:,}"
    )

    print(
        f"Months per company: {months}"
    )

    print(
        f"Expected rows: "
        f"{companies * months:,}"
    )

    print(
        f"Actual rows: "
        f"{len(df):,}"
    )

    if len(df) != companies * months:
        raise ValueError(
            "Dataset shape is not rectangular."
        )

    # ========================================================
    # CURRENT SCORE
    # ========================================================

    print(
        "\nCalculating current health scores..."
    )

    df["current_score"] = (
        calculate_current_scores(df)
    )

    df["current_label"] = (
        labels_from_scores(
            df["current_score"].to_numpy()
        )
    )

    # ========================================================
    # FUTURE TARGETS
    # ========================================================

    print(
        "\nCalculating future targets..."
    )

    for horizon in [1, 2, 3]:

        print(
            f"  Calculating "
            f"{horizon}-month target..."
        )

        scores = calculate_future_targets(
            df,
            horizon,
        )

        score_column = (
            f"target_{horizon}m_score"
        )

        label_column = (
            f"target_{horizon}m_label"
        )

        df[score_column] = (
            scores.reshape(-1)
        )

        df[label_column] = (
            labels_from_scores(
                df[score_column].to_numpy()
            )
        )

        print(
            f"  Completed "
            f"{horizon}-month target."
        )

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_ground_truth(df):

    print(
        "\n" + "=" * 70
    )

    print(
        "GROUND TRUTH VALIDATION"
    )

    print(
        "=" * 70
    )

    print(
        f"\nRows: {len(df):,}"
    )

    print(
        f"Companies: "
        f"{df['company_id'].nunique():,}"
    )

    # --------------------------------------------------------
    # Score ranges
    # --------------------------------------------------------

    score_columns = [
        "current_score",
        "target_1m_score",
        "target_2m_score",
        "target_3m_score",
    ]

    print(
        "\nScore ranges:"
    )

    for column in score_columns:

        valid = df[column].dropna()

        print(
            f"\n{column}"
        )

        print(
            f"  Count: "
            f"{len(valid):,}"
        )

        print(
            f"  Min:   "
            f"{valid.min():.2f}"
        )

        print(
            f"  Max:   "
            f"{valid.max():.2f}"
        )

        print(
            f"  Mean:  "
            f"{valid.mean():.2f}"
        )

        print(
            f"  Median:"
            f" {valid.median():.2f}"
        )

        assert valid.min() >= 0
        assert valid.max() <= 100

    # --------------------------------------------------------
    # Label distributions
    # --------------------------------------------------------

    label_columns = [
        "current_label",
        "target_1m_label",
        "target_2m_label",
        "target_3m_label",
    ]

    print(
        "\n" + "=" * 70
    )

    print(
        "LABEL DISTRIBUTIONS"
    )

    print(
        "=" * 70
    )

    for column in label_columns:

        print(
            f"\n{column}"
        )

        counts = (
            df[column]
            .value_counts(
                dropna=False
            )
        )

        percentages = (
            df[column]
            .value_counts(
                normalize=True,
                dropna=False,
            )
            .mul(100)
            .round(2)
        )

        print(
            "Counts:"
        )

        print(
            counts
        )

        print(
            "Percentages:"
        )

        print(
            percentages
        )

    # --------------------------------------------------------
    # Deficit safety override
    # --------------------------------------------------------

    deficit_mask = (
        df["unfunded_deficit"]
        > 0
    )

    deficit_count = (
        deficit_mask.sum()
    )

    critical_count = (
        (
            df.loc[
                deficit_mask,
                "current_label"
            ]
            == "Critical"
        )
        .sum()
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "DEFICIT SAFETY CHECK"
    )

    print(
        "=" * 70
    )

    print(
        f"Deficit rows: "
        f"{deficit_count:,}"
    )

    print(
        f"Deficit rows labelled Critical: "
        f"{critical_count:,}"
    )

    if deficit_count > 0:
        assert (
            critical_count
            == deficit_count
        ), (
            "Some current deficit rows "
            "were not labelled Critical."
        )

    print(
        "\nGround truth validation PASSED."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "FINSHIELD - GROUND TRUTH ENGINE"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print(
        f"\nLoading dataset:"
    )

    print(
        f"  {INPUT_FILE}"
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\nLoaded:"
    )

    print(
        f"  Rows: "
        f"{len(df):,}"
    )

    print(
        f"  Companies: "
        f"{df['company_id'].nunique():,}"
    )

    # --------------------------------------------------------
    # Derived metric
    # --------------------------------------------------------

    df["credit_utilization"] = (
        df["credit_balance"]
        / df["credit_limit"].replace(
            0,
            np.nan,
        )
    )

    # --------------------------------------------------------
    # Create ground truth
    # --------------------------------------------------------

    df = create_ground_truth(
        df
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_ground_truth(
        df
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\nSaving ground-truth dataset..."
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "GROUND TRUTH DATASET SAVED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nFile:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )

    print(
        "\nFinShield ground-truth generation "
        "completed successfully."
    )