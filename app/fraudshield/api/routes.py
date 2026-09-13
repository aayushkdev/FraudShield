from fastapi import APIRouter, Query

from fraudshield.schema.api import AlertLifecycleUpdate, TransactionAccepted, TransactionCreate
from fraudshield.services.transaction_service import accept_transaction, get_transaction_detail, get_transaction_scores, get_transaction_summary, get_user_profiles, update_transaction_alert

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


@router.get("/transactions/{txn_id}")
def get_transaction(txn_id: int):
    return get_transaction_detail(txn_id)


@router.get("/analytics/profiles")
def get_profiles():
    return get_user_profiles()


@router.patch("/alerts/{txn_id}")
def update_alert_status(txn_id: int, update: AlertLifecycleUpdate):
    return update_transaction_alert(txn_id, update.status, update.actor)
