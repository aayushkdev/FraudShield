from sqlalchemy import Column, DateTime, Numeric, String

from fraudshield.models.base import Base


class Transaction(Base):
    __tablename__ = "TRANSACTIONS"
    __table_args__ = {"schema": "FRAUDSHIELD"}

    txn_id = Column(Numeric(18, 0), primary_key=True)
    user_id = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    city = Column(String(50), nullable=False)
    merchant = Column(String(100), nullable=False)
    txn_time = Column(DateTime, nullable=False)
