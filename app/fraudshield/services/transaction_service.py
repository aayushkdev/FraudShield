from fraudshield.db.queries import get_profiles, get_scores, get_summary, get_transaction, insert_transaction, update_alert
from fraudshield.schema.api import TransactionCreate
from fraudshield.services.notifications import notify_high_risk


def accept_transaction(transaction: TransactionCreate) -> dict:
    insert_transaction(transaction)
    scored = get_transaction(transaction.txn_id)
    if scored:
        notify_high_risk(scored)
    return {"txn_id": transaction.txn_id, "status": "accepted"}


def get_transaction_scores(limit: int = 500) -> list[dict]:
    return get_scores(limit)


def get_transaction_summary() -> dict:
    return get_summary()


def get_transaction_detail(txn_id: int) -> dict | None:
    return get_transaction(txn_id)


def get_user_profiles() -> list[dict]:
    return get_profiles()


def update_transaction_alert(txn_id: int, status: str, actor: str) -> dict:
    update_alert(txn_id, status, actor)
    return {"txn_id": txn_id, "status": status, "actor": actor}
