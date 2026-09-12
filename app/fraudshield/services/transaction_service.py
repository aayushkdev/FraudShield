from fraudshield.db.queries import get_scores, get_summary, insert_transaction
from fraudshield.schema.api import TransactionCreate


def accept_transaction(transaction: TransactionCreate) -> dict:
    insert_transaction(transaction)
    return {"txn_id": transaction.txn_id, "status": "accepted"}


def get_transaction_scores(limit: int = 500) -> list[dict]:
    return get_scores(limit)


def get_transaction_summary() -> dict:
    return get_summary()
