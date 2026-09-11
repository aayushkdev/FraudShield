from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    txn_id: int = Field(gt=0)
    user_id: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    city: str = Field(min_length=1, max_length=50)
    merchant: str = Field(min_length=1, max_length=100)
    txn_time: datetime


class TransactionAccepted(BaseModel):
    txn_id: int
    status: str = "accepted"
