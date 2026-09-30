"""
FinShield - Cash Flow Simulation Engine

Connects:
    Revenue
    Working Capital
    Expenses
    Debt
    Credit Facility

Produces:
    Beginning cash
    Operating inflows
    Operating outflows
    Financing activity
    Ending cash
    Available credit
    Available liquidity
    Unfunded deficit
"""

from config import RANDOM_SEED


# ============================================================
# CREDIT DRAW
# ============================================================

def calculate_credit_draw(
    cash_before_financing,
    credit_available
):

    if cash_before_financing >= 0:
        return 0.0

    required_cash = abs(
        cash_before_financing
    )

    return min(
        required_cash,
        credit_available
    )


# ============================================================
# CREDIT REPAYMENT
# ============================================================

def calculate_credit_repayment(
    credit_balance,
    cash_before_financing
):

    if credit_balance <= 0:
        return 0.0

    if cash_before_financing <= 0:
        return 0.0

    # Keep half of excess cash as liquidity.
    repayment_capacity = (
        cash_before_financing
        * 0.50
    )

    return min(
        credit_balance,
        repayment_capacity
    )


# ============================================================
# MAIN CASH ENGINE
# ============================================================

def simulate_cash_flow(
    company,
    working_capital,
    expenses,
    debt_schedule,
    planned_capex=None
):

    if planned_capex is None:

        planned_capex = [
            0.0
            for _ in working_capital
        ]

    if not (
        len(working_capital)
        == len(expenses)
        == len(debt_schedule)
        == len(planned_capex)
    ):

        raise ValueError(
            "All financial trajectories must "
            "have the same number of months."
        )

    beginning_cash = float(
        company["starting_cash"]
    )

    beginning_credit_balance = float(
        company["credit_balance"]
    )

    credit_limit = float(
        company["credit_limit"]
    )

    results = []

    for month_index in range(
        len(working_capital)
    ):

        wc = working_capital[
            month_index
        ]

        exp = expenses[
            month_index
        ]

        debt = debt_schedule[
            month_index
        ]

        capex = planned_capex[
            month_index
        ]

        # ====================================================
        # INFLOWS
        # ====================================================

        cash_sales = wc[
            "cash_sales"
        ]

        customer_collections = wc[
            "collections"
        ]

        operating_inflows = (
            cash_sales
            + customer_collections
        )

        # ====================================================
        # OUTFLOWS
        # ====================================================

        supplier_payments = wc[
            "supplier_payments"
        ]

        cash_purchases = wc[
            "cash_purchases"
        ]

        payroll = exp[
            "payroll"
        ]

        rent = exp[
            "rent"
        ]

        utilities = exp[
            "utilities"
        ]

        marketing = exp[
            "marketing"
        ]

        insurance = exp[
            "insurance"
        ]

        other_expenses = exp[
            "other_expenses"
        ]

        tax_payment = exp[
            "tax_provision"
        ]

        loan_interest = debt[
            "interest_payment"
        ]

        loan_principal = debt[
            "principal_payment"
        ]

        total_cash_outflow = (
            supplier_payments
            + cash_purchases
            + payroll
            + rent
            + utilities
            + marketing
            + insurance
            + other_expenses
            + tax_payment
            + loan_interest
            + loan_principal
            + capex
        )

        # ====================================================
        # CASH BEFORE FINANCING
        # ====================================================

        cash_before_financing = (
            beginning_cash
            + operating_inflows
            - total_cash_outflow
        )

        # ====================================================
        # CREDIT
        # ====================================================

        available_credit_before = max(
            credit_limit
            - beginning_credit_balance,
            0.0
        )

        credit_draw = calculate_credit_draw(
            cash_before_financing,
            available_credit_before
        )

        cash_after_draw = (
            cash_before_financing
            + credit_draw
        )

        credit_balance_after_draw = (
            beginning_credit_balance
            + credit_draw
        )

        credit_repayment = (
            calculate_credit_repayment(
                credit_balance_after_draw,
                cash_after_draw
            )
        )

        ending_credit_balance = max(
            credit_balance_after_draw
            - credit_repayment,
            0.0
        )

        # ====================================================
        # ENDING CASH
        # ====================================================

        ending_cash = max(
            cash_after_draw
            - credit_repayment,
            0.0
        )

        # ====================================================
        # DEFICIT
        # ====================================================

        cash_after_available_credit = (
            cash_before_financing
            + credit_draw
        )

        unfunded_deficit = max(
            -cash_after_available_credit,
            0.0
        )

        # ====================================================
        # LIQUIDITY
        # ====================================================

        available_credit_after = max(
            credit_limit
            - ending_credit_balance,
            0.0
        )

        available_liquidity = (
            ending_cash
            + available_credit_after
        )

        # ====================================================
        # NET CASH FLOW
        # ====================================================

        net_cash_flow = (
            operating_inflows
            - total_cash_outflow
        )

        # ====================================================
        # SAVE
        # ====================================================

        results.append(
            {
                "company_id":
                    company["company_id"],

                "month_index":
                    wc["month_index"],

                "month":
                    wc["month"],

                "beginning_cash":
                    beginning_cash,

                "operating_inflows":
                    operating_inflows,

                "total_cash_outflow":
                    total_cash_outflow,

                "cash_before_financing":
                    cash_before_financing,

                "credit_draw":
                    credit_draw,

                "credit_repayment":
                    credit_repayment,

                "ending_cash":
                    ending_cash,

                "credit_limit":
                    credit_limit,

                "beginning_credit_balance":
                    beginning_credit_balance,

                "ending_credit_balance":
                    ending_credit_balance,

                "available_credit":
                    available_credit_after,

                "available_liquidity":
                    available_liquidity,

                "unfunded_deficit":
                    unfunded_deficit,

                "net_cash_flow":
                    net_cash_flow,

                "cash_sales":
                    cash_sales,

                "customer_collections":
                    customer_collections,

                "supplier_payments":
                    supplier_payments,

                "cash_purchases":
                    cash_purchases,

                "payroll":
                    payroll,

                "rent":
                    rent,

                "utilities":
                    utilities,

                "marketing":
                    marketing,

                "insurance":
                    insurance,

                "other_expenses":
                    other_expenses,

                "tax_payment":
                    tax_payment,

                "loan_interest":
                    loan_interest,

                "loan_principal":
                    loan_principal,

                "capex":
                    capex,

                "revenue":
                    wc["revenue"],

                "accounts_receivable":
                    wc[
                        "accounts_receivable"
                    ],

                "inventory":
                    wc["inventory"],

                "accounts_payable":
                    wc[
                        "accounts_payable"
                    ],

                "debt_balance":
                    debt[
                        "ending_debt_balance"
                    ],
            }
        )

        beginning_cash = ending_cash

        beginning_credit_balance = (
            ending_credit_balance
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_cash_summary(results):

    latest = results[-1]

    minimum_cash = min(
        row["ending_cash"]
        for row in results
    )

    maximum_deficit = max(
        row["unfunded_deficit"]
        for row in results
    )

    maximum_credit_utilization = max(
        (
            row["ending_credit_balance"]
            / row["credit_limit"]
            if row["credit_limit"] > 0
            else 0.0
        )
        for row in results
    )

    print("\n" + "=" * 75)
    print(
        "FINSHIELD CASH FLOW ENGINE"
    )
    print("=" * 75)

    print(
        f"Months simulated: "
        f"{len(results)}"
    )

    print(
        f"\nLatest month: "
        f"{latest['month']}"
    )

    print(
        f"Beginning cash: "
        f"₹{latest['beginning_cash']:,.0f}"
    )

    print(
        f"Operating inflows: "
        f"₹{latest['operating_inflows']:,.0f}"
    )

    print(
        f"Cash outflows: "
        f"₹{latest['total_cash_outflow']:,.0f}"
    )

    print(
        f"Cash before financing: "
        f"₹{latest['cash_before_financing']:,.0f}"
    )

    print(
        f"Credit draw: "
        f"₹{latest['credit_draw']:,.0f}"
    )

    print(
        f"Credit repayment: "
        f"₹{latest['credit_repayment']:,.0f}"
    )

    print(
        f"Ending cash: "
        f"₹{latest['ending_cash']:,.0f}"
    )

    print(
        f"Credit balance: "
        f"₹{latest['ending_credit_balance']:,.0f}"
    )

    print(
        f"Available credit: "
        f"₹{latest['available_credit']:,.0f}"
    )

    print(
        f"Available liquidity: "
        f"₹{latest['available_liquidity']:,.0f}"
    )

    print(
        f"\nMinimum cash during simulation: "
        f"₹{minimum_cash:,.0f}"
    )

    print(
        f"Maximum unfunded deficit: "
        f"₹{maximum_deficit:,.0f}"
    )

    print(
        f"Maximum credit utilization: "
        f"{maximum_credit_utilization * 100:.1f}%"
    )

    print("\nFirst 6 months:")

    for row in results[:6]:

        print(
            f"  {row['month']} | "
            f"Cash ₹{row['ending_cash']:,.0f} | "
            f"Credit ₹{row['ending_credit_balance']:,.0f} | "
            f"Liquidity ₹{row['available_liquidity']:,.0f}"
        )

    print("=" * 75)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from company_generator import (
        generate_companies
    )

    from revenue_engine import (
        generate_revenue_trajectory
    )

    from working_capital import (
        simulate_working_capital
    )

    from expense_engine import (
        simulate_expenses
    )

    from debt_engine import (
        generate_debt_schedule
    )

    companies = generate_companies(
        total_companies=1
    )

    company = companies[0]

    revenue = generate_revenue_trajectory(
        company=company,
        months=36
    )

    working_capital = (
        simulate_working_capital(
            company=company,
            revenue_trajectory=revenue
        )
    )

    expenses = simulate_expenses(
        company=company,
        financial_trajectory=working_capital
    )

    loan, debt_schedule = (
        generate_debt_schedule(
            company=company,
            months=36
        )
    )

    cash_flow = simulate_cash_flow(
        company=company,
        working_capital=working_capital,
        expenses=expenses,
        debt_schedule=debt_schedule
    )

    print(
        f"\nTesting company: "
        f"{company['company_id']}"
    )

    print(
        f"Sector: "
        f"{company['sector']}"
    )

    print(
        f"Company size: "
        f"{company['company_size']}"
    )

    print_cash_summary(
        cash_flow
    )