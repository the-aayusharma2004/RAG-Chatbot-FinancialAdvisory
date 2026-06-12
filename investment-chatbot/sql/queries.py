from sql.database import get_session
from sql.models import User, Portfolio, Transaction, Goal, InvestmentProduct


def get_user_profile(user_id: int) -> dict | None:
    """Return user profile data as a dict, or None if not found."""
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "monthly_income": float(user.monthly_income),
            "risk_appetite": user.risk_appetite,
            "investment_goal": user.investment_goal,
            "investment_horizon": user.investment_horizon,
        }
    finally:
        session.close()


def get_user_portfolio(user_id: int) -> list[dict]:
    """Return all portfolio holdings for a user with product details."""
    session = get_session()
    try:
        rows = (
            session.query(Portfolio, InvestmentProduct)
            .join(InvestmentProduct, Portfolio.product_id == InvestmentProduct.product_id)
            .filter(Portfolio.user_id == user_id)
            .all()
        )
        result = []
        for p, prod in rows:
            invested = float(p.amount_invested)
            current = float(p.current_value)
            gain_pct = ((current - invested) / invested * 100) if invested else 0
            result.append({
                "portfolio_id": p.portfolio_id,
                "product_name": prod.product_name,
                "category": prod.category,
                "risk_level": prod.risk_level,
                "amount_invested": invested,
                "current_value": current,
                "gain_loss": round(current - invested, 2),
                "gain_pct": round(gain_pct, 2),
                "purchase_date": str(p.purchase_date),
            })
        return result
    finally:
        session.close()


def get_total_investment(user_id: int) -> dict:
    """Return total invested, current value, and overall gain/loss."""
    session = get_session()
    try:
        rows = session.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        total_invested = sum(float(r.amount_invested) for r in rows)
        total_current = sum(float(r.current_value) for r in rows)
        gain = total_current - total_invested
        gain_pct = (gain / total_invested * 100) if total_invested else 0
        return {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_gain_loss": round(gain, 2),
            "overall_gain_pct": round(gain_pct, 2),
            "num_holdings": len(rows),
        }
    finally:
        session.close()


def get_transactions(user_id: int, limit: int = 10) -> list[dict]:
    """Return recent transactions for a user."""
    session = get_session()
    try:
        rows = (
            session.query(Transaction, InvestmentProduct)
            .join(InvestmentProduct, Transaction.product_id == InvestmentProduct.product_id)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "transaction_id": t.transaction_id,
                "product_name": prod.product_name,
                "amount": float(t.amount),
                "type": t.transaction_type,
                "date": str(t.transaction_date),
            }
            for t, prod in rows
        ]
    finally:
        session.close()


def get_goals(user_id: int) -> list[dict]:
    """Return all financial goals and progress for a user."""
    session = get_session()
    try:
        rows = session.query(Goal).filter(Goal.user_id == user_id).all()
        result = []
        for g in rows:
            target = float(g.target_amount)
            progress = float(g.current_progress)
            pct = (progress / target * 100) if target else 0
            result.append({
                "goal_id": g.goal_id,
                "goal_name": g.goal_name,
                "target_amount": target,
                "current_progress": progress,
                "progress_pct": round(pct, 2),
                "target_date": str(g.target_date),
                "remaining": round(target - progress, 2),
            })
        return result
    finally:
        session.close()


def portfolio_to_context_text(user_id: int) -> str:
    """Convert portfolio data to a plain-text context string for the LLM."""
    summary = get_total_investment(user_id)
    holdings = get_user_portfolio(user_id)

    if not holdings:
        return "No portfolio data found for this user."

    lines = [
        f"Total Invested: Rs.{summary['total_invested']:,.0f}",
        f"Current Value:  Rs.{summary['total_current_value']:,.0f}",
        f"Overall Gain/Loss: Rs.{summary['total_gain_loss']:,.0f} ({summary['overall_gain_pct']:.1f}%)",
        f"Number of Holdings: {summary['num_holdings']}",
        "",
        "Holdings breakdown:",
    ]
    for h in holdings:
        lines.append(
            f"  - {h['product_name']} ({h['category']}, {h['risk_level']} risk): "
            f"Invested Rs.{h['amount_invested']:,.0f}, "
            f"Current Rs.{h['current_value']:,.0f}, "
            f"Gain {h['gain_pct']:+.1f}%"
        )
    return "\n".join(lines)


def goals_to_context_text(user_id: int) -> str:
    """Convert goals data to plain-text context for the LLM."""
    goals = get_goals(user_id)
    if not goals:
        return "No financial goals defined for this user."
    lines = ["Financial Goals:"]
    for g in goals:
        lines.append(
            f"  - {g['goal_name']}: Rs.{g['current_progress']:,.0f} / "
            f"Rs.{g['target_amount']:,.0f} ({g['progress_pct']:.1f}% complete), "
            f"target date {g['target_date']}, Rs.{g['remaining']:,.0f} remaining"
        )
    return "\n".join(lines)
