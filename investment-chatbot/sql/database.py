import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "financial_advisor")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal()


def init_db():
    """Create all tables if they don't exist and seed sample data."""
    from sql.models import Base as ModelBase
    engine = get_engine()
    ModelBase.metadata.create_all(bind=engine)
    print("Database tables created (or already exist).")
    _seed_sample_data()


def _seed_sample_data():
    """Insert sample data only if tables are empty."""
    from sql.models import User, InvestmentProduct, Portfolio, Transaction, Goal
    import datetime

    session = get_session()
    try:
        if session.query(User).count() > 0:
            print("Sample data already present. Skipping seed.")
            return

        print("Seeding sample data...")

        users = [
            User(name="Arjun Sharma", age=28, monthly_income=60000,
                 risk_appetite="medium", investment_goal="wealth growth",
                 investment_horizon="long"),
            User(name="Priya Nair", age=45, monthly_income=120000,
                 risk_appetite="low", investment_goal="retirement",
                 investment_horizon="long"),
            User(name="Rohit Verma", age=32, monthly_income=85000,
                 risk_appetite="high", investment_goal="wealth growth",
                 investment_horizon="medium"),
        ]
        session.add_all(users)
        session.flush()

        products = [
            InvestmentProduct(product_name="Equity Mutual Fund", category="Mutual Fund",
                              risk_level="high", expected_return=12.00, minimum_investment=1000),
            InvestmentProduct(product_name="Debt Mutual Fund", category="Mutual Fund",
                              risk_level="low", expected_return=7.00, minimum_investment=1000),
            InvestmentProduct(product_name="ELSS Fund", category="Tax Saving",
                              risk_level="high", expected_return=13.00, minimum_investment=500),
            InvestmentProduct(product_name="Fixed Deposit", category="Fixed Income",
                              risk_level="very low", expected_return=6.75, minimum_investment=10000),
            InvestmentProduct(product_name="PPF", category="Government Scheme",
                              risk_level="none", expected_return=7.10, minimum_investment=500),
            InvestmentProduct(product_name="NPS", category="Retirement",
                              risk_level="medium", expected_return=9.00, minimum_investment=500),
        ]
        session.add_all(products)
        session.flush()

        portfolios = [
            Portfolio(user_id=users[0].user_id, product_id=products[0].product_id,
                      amount_invested=50000, current_value=58000,
                      purchase_date=datetime.date(2023, 1, 15)),
            Portfolio(user_id=users[0].user_id, product_id=products[2].product_id,
                      amount_invested=30000, current_value=36000,
                      purchase_date=datetime.date(2023, 3, 10)),
            Portfolio(user_id=users[1].user_id, product_id=products[4].product_id,
                      amount_invested=150000, current_value=165000,
                      purchase_date=datetime.date(2021, 6, 1)),
            Portfolio(user_id=users[1].user_id, product_id=products[3].product_id,
                      amount_invested=200000, current_value=220000,
                      purchase_date=datetime.date(2022, 1, 1)),
            Portfolio(user_id=users[2].user_id, product_id=products[0].product_id,
                      amount_invested=100000, current_value=125000,
                      purchase_date=datetime.date(2022, 8, 20)),
        ]
        session.add_all(portfolios)
        session.flush()

        transactions = [
            Transaction(user_id=users[0].user_id, product_id=products[0].product_id,
                        amount=50000, transaction_type="buy"),
            Transaction(user_id=users[0].user_id, product_id=products[2].product_id,
                        amount=30000, transaction_type="buy"),
            Transaction(user_id=users[1].user_id, product_id=products[4].product_id,
                        amount=150000, transaction_type="buy"),
            Transaction(user_id=users[2].user_id, product_id=products[0].product_id,
                        amount=100000, transaction_type="buy"),
            Transaction(user_id=users[2].user_id, product_id=products[0].product_id,
                        amount=10000, transaction_type="sip"),
        ]
        session.add_all(transactions)

        goals = [
            Goal(user_id=users[0].user_id, goal_name="Emergency Fund",
                 target_amount=180000, target_date=datetime.date(2025, 12, 31),
                 current_progress=80000),
            Goal(user_id=users[1].user_id, goal_name="Retirement Corpus",
                 target_amount=10000000, target_date=datetime.date(2035, 3, 31),
                 current_progress=385000),
            Goal(user_id=users[2].user_id, goal_name="House Down Payment",
                 target_amount=1500000, target_date=datetime.date(2026, 12, 31),
                 current_progress=125000),
        ]
        session.add_all(goals)

        session.commit()
        print("Sample data seeded successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error seeding data: {e}")
    finally:
        session.close()


def test_connection() -> dict:
    """Quick connectivity check used by the /status route."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": MYSQL_DATABASE, "host": MYSQL_HOST}
    except Exception as e:
        return {"status": f"error: {e}", "database": MYSQL_DATABASE, "host": MYSQL_HOST}
