from dataclasses import dataclass, field


@dataclass
class UserProfile:
    age: int
    monthly_income: float
    risk_appetite: str        # "low" | "medium" | "high"
    investment_goal: str      # e.g. "retirement", "wealth growth", "child education"
    investment_horizon: str   # "short" | "medium" | "long"
    existing_investments: list = field(default_factory=list)


def profile_to_query(profile: UserProfile) -> str:
    """Convert a UserProfile into a natural language retrieval query."""
    existing = (
        f"already has {', '.join(profile.existing_investments)}"
        if profile.existing_investments
        else "no existing investments"
    )
    return (
        f"investment options for {profile.age} year old, "
        f"monthly income Rs.{profile.monthly_income:,.0f}, "
        f"{profile.risk_appetite} risk appetite, "
        f"goal: {profile.investment_goal}, "
        f"{profile.investment_horizon}-term investment horizon, "
        f"{existing}"
    )
