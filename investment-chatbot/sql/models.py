from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sql.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    age = Column(Integer)
    monthly_income = Column(Numeric(12, 2))
    risk_appetite = Column(String(20))
    investment_goal = Column(String(100))
    investment_horizon = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    goals = relationship("Goal", back_populates="user")


class InvestmentProduct(Base):
    __tablename__ = "investment_products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(100))
    category = Column(String(50))
    risk_level = Column(String(20))
    expected_return = Column(Numeric(5, 2))
    minimum_investment = Column(Numeric(12, 2))

    portfolio_entries = relationship("Portfolio", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")


class Portfolio(Base):
    __tablename__ = "portfolio"

    portfolio_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("investment_products.product_id"))
    amount_invested = Column(Numeric(12, 2))
    current_value = Column(Numeric(12, 2))
    purchase_date = Column(Date)

    user = relationship("User", back_populates="portfolio")
    product = relationship("InvestmentProduct", back_populates="portfolio_entries")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("investment_products.product_id"))
    amount = Column(Numeric(12, 2))
    transaction_type = Column(String(20))  # buy | sell | sip | redeem
    transaction_date = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="transactions")
    product = relationship("InvestmentProduct", back_populates="transactions")


class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    goal_name = Column(String(100))
    target_amount = Column(Numeric(12, 2))
    target_date = Column(Date)
    current_progress = Column(Numeric(12, 2))

    user = relationship("User", back_populates="goals")
