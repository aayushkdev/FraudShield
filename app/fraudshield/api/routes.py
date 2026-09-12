from fastapi import APIRouter, Query

from fraudshield.schema.api import TransactionAccepted, TransactionCreate
from fraudshield.services.transaction_service import accept_transaction, get_transaction_scores, get_transaction_summary

router = APIRouter(prefix="/api/v1", tags=["fraud"])


@router.post("/transactions", response_model=TransactionAccepted, status_code=201)
def create_transaction(transaction: TransactionCreate):
    return accept_transaction(transaction)


@router.get("/analytics/scores")
def get_scores(limit: int = Query(default=500, ge=1, le=5000)):
    return get_transaction_scores(limit)


@router.get("/analytics/summary")
def get_summary():
    return get_transaction_summary()
