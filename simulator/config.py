"""
FinShield - Simulation Configuration

Central configuration for synthetic Indian SME financial simulation.

IMPORTANT:
These parameters are simulation assumptions calibrated around
Indian SME/sector characteristics. They are NOT observed records
of individual companies.
"""

# ============================================================
# GLOBAL SETTINGS
# ============================================================

RANDOM_SEED = 42

START_DATE = "2023-01-01"

HISTORY_MONTHS = 36

# Development stages
PROTOTYPE_COMPANIES = 50
VALIDATION_COMPANIES = 100
SMALL_SAMPLE_COMPANIES = 1_000
MEDIUM_SAMPLE_COMPANIES = 10_000
FINAL_COMPANIES = 100_000


# ============================================================
# COMPANY SIZE PROFILES
# ============================================================

SIZE_PROFILES = {

    "micro": {
        "annual_revenue_min": 5_000_000,
        "annual_revenue_max": 100_000_000,

        "employees_min": 3,
        "employees_max": 50,

        "starting_cash_months_min": 1.0,
        "starting_cash_months_max": 6.0,

        "debt_intensity": (0.05, 0.60),
        "credit_utilization": (0.10, 0.80),
    },

    "small": {
        "annual_revenue_min": 50_000_000,
        "annual_revenue_max": 1_000_000_000,

        "employees_min": 20,
        "employees_max": 300,

        "starting_cash_months_min": 1.5,
        "starting_cash_months_max": 6.0,

        "debt_intensity": (0.10, 0.75),
        "credit_utilization": (0.10, 0.85),
    },

    "medium": {
        "annual_revenue_min": 500_000_000,
        "annual_revenue_max": 5_000_000_000,

        "employees_min": 100,
        "employees_max": 2_000,

        "starting_cash_months_min": 2.0,
        "starting_cash_months_max": 6.0,

        "debt_intensity": (0.15, 0.90),
        "credit_utilization": (0.10, 0.90),
    },
}


# ============================================================
# SECTOR PROFILES
# ============================================================

SECTOR_PROFILES = {

    # --------------------------------------------------------
    # RETAIL
    # --------------------------------------------------------

    "retail": {

        "subtypes": [
            "grocery_fmcg",
            "apparel",
            "electronics",
            "general_retail",
        ],

        "cogs_margin": (0.60, 0.85),

        "cash_sales_pct": {
            "micro": (0.70, 0.98),
            "small": (0.60, 0.95),
            "medium": (0.50, 0.90),
        },

        "dso_days": {
            "micro": (5, 45),
            "small": (7, 50),
            "medium": (10, 60),
        },

        "inventory_days": {
            "micro": (20, 90),
            "small": (25, 90),
            "medium": (30, 100),
        },

        "dpo_days": {
            "micro": (20, 75),
            "small": (25, 85),
            "medium": (30, 90),
        },

        "payroll_intensity": "medium",
        "rent_intensity": "high",
        "debt_intensity": "low_medium",

        "seasonality_strength": 0.15,
    },


    # --------------------------------------------------------
    # WHOLESALE & DISTRIBUTION
    # --------------------------------------------------------

    "wholesale": {

        "subtypes": [
            "fmcg_distribution",
            "electronics_distribution",
            "apparel_distribution",
            "industrial_supplies",
        ],

        "cogs_margin": (0.70, 0.90),

        "cash_sales_pct": {
            "micro": (0.10, 0.50),
            "small": (0.05, 0.40),
            "medium": (0.05, 0.30),
        },

        "dso_days": {
            "micro": (30, 120),
            "small": (30, 120),
            "medium": (30, 120),
        },

        "inventory_days": {
            "micro": (15, 120),
            "small": (20, 120),
            "medium": (20, 120),
        },

        "dpo_days": {
            "micro": (30, 90),
            "small": (30, 120),
            "medium": (30, 120),
        },

        "payroll_intensity": "medium",
        "rent_intensity": "medium",
        "debt_intensity": "medium_high",

        "seasonality_strength": 0.12,
    },


    # --------------------------------------------------------
    # MANUFACTURING
    # --------------------------------------------------------

    "manufacturing": {

        "subtypes": [
            "food_processing",
            "textiles",
            "auto_components",
            "consumer_products",
            "industrial_products",
        ],

        "cogs_margin": (0.55, 0.85),

        "cash_sales_pct": {
            "micro": (0.10, 0.40),
            "small": (0.05, 0.30),
            "medium": (0.05, 0.25),
        },

        "dso_days": {
            "micro": (30, 120),
            "small": (30, 120),
            "medium": (30, 120),
        },

        "inventory_days": {
            "micro": (30, 120),
            "small": (30, 120),
            "medium": (30, 150),
        },

        "dpo_days": {
            "micro": (30, 120),
            "small": (30, 120),
            "medium": (30, 150),
        },

        "payroll_intensity": "medium_high",
        "rent_intensity": "medium",
        "debt_intensity": "high",

        "seasonality_strength": 0.10,
    },


    # --------------------------------------------------------
    # FOOD & HOSPITALITY
    # --------------------------------------------------------

    "food_hospitality": {

        "subtypes": [
            "restaurant",
            "cafe",
            "catering",
            "hotel",
            "cloud_kitchen",
        ],

        "cogs_margin": (0.25, 0.50),

        "cash_sales_pct": {
            "micro": (0.60, 0.95),
            "small": (0.50, 0.90),
            "medium": (0.40, 0.85),
        },

        "dso_days": {
            "micro": (5, 45),
            "small": (5, 60),
            "medium": (10, 75),
        },

        "inventory_days": {
            "micro": (3, 30),
            "small": (3, 30),
            "medium": (3, 45),
        },

        "dpo_days": {
            "micro": (15, 60),
            "small": (20, 75),
            "medium": (20, 90),
        },

        "payroll_intensity": "very_high",
        "rent_intensity": "high",
        "debt_intensity": "medium",

        "seasonality_strength": 0.20,
    },


    # --------------------------------------------------------
    # PROFESSIONAL SERVICES
    # --------------------------------------------------------

    "professional_services": {

        "subtypes": [
            "it_services",
            "consulting",
            "marketing",
            "accounting",
            "legal_business_services",
        ],

        "cogs_margin": (0.10, 0.40),

        "cash_sales_pct": {
            "micro": (0.10, 0.40),
            "small": (0.05, 0.30),
            "medium": (0.05, 0.25),
        },

        "dso_days": {
            "micro": (30, 120),
            "small": (30, 120),
            "medium": (30, 150),
        },

        "inventory_days": {
            "micro": (0, 5),
            "small": (0, 5),
            "medium": (0, 10),
        },

        "dpo_days": {
            "micro": (15, 60),
            "small": (20, 75),
            "medium": (20, 90),
        },

        "payroll_intensity": "very_high",
        "rent_intensity": "medium",
        "debt_intensity": "low_medium",

        "seasonality_strength": 0.08,
    },
}


# ============================================================
# SHOCK SEVERITY
# ============================================================

SHOCK_SEVERITY = {

    "mild": {
        "revenue_change": (-0.10, -0.05),
        "dso_increase": (10, 15),
        "inventory_days_increase": (10, 20),
        "cogs_increase": (0.03, 0.07),
    },

    "moderate": {
        "revenue_change": (-0.20, -0.10),
        "dso_increase": (20, 35),
        "inventory_days_increase": (20, 40),
        "cogs_increase": (0.07, 0.15),
    },

    "severe": {
        "revenue_change": (-0.40, -0.20),
        "dso_increase": (35, 60),
        "inventory_days_increase": (40, 80),
        "cogs_increase": (0.15, 0.30),
    },
}


# ============================================================
# RISK THRESHOLDS
# ============================================================

RISK_THRESHOLDS = {

    "good_min": 70,
    "watch_min": 40,
    "critical_min": 0,

}


# ============================================================
# HEALTH SCORE WEIGHTS
# ============================================================

HEALTH_SCORE_WEIGHTS = {

    "liquidity_resilience": 0.30,
    "forecast_cash_stress": 0.30,
    "working_capital_health": 0.15,
    "debt_service_health": 0.15,
    "cash_flow_stability": 0.10,

}


# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """Basic configuration validation."""

    expected_sectors = {
        "retail",
        "wholesale",
        "manufacturing",
        "food_hospitality",
        "professional_services",
    }

    assert set(SECTOR_PROFILES.keys()) == expected_sectors

    expected_sizes = {
        "micro",
        "small",
        "medium",
    }

    assert set(SIZE_PROFILES.keys()) == expected_sizes

    assert sum(HEALTH_SCORE_WEIGHTS.values()) == 1.0

    print("FinShield configuration validated successfully.")


if __name__ == "__main__":
    validate_config()