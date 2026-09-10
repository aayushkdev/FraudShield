from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from fraudshield.models.base import Base


class Transaction(Base):
    __tablename__ = "TRANSACTIONS"
    __table_args__ = {"schema": "FRAUDSHIELD"}

    txn_id: Mapped[Decimal] = mapped_column(Numeric(18, 0), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    merchant: Mapped[str] = mapped_column(String(100), nullable=False)
    txn_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
