from sqlalchemy import text

from fraudshield.db.connection import ENGINE
from fraudshield.schema.api import TransactionCreate

SCORES_QUERY = """
    SELECT *
    FROM FRAUDSHIELD.FRAUD_SCORES
    ORDER BY TXN_TIME DESC
    LIMIT :limit
"""

SUMMARY_QUERY = """
    SELECT
        COUNT(*) AS total_transactions,
        SUM(CASE WHEN STATUS = 'FRAUD' THEN 1 ELSE 0 END) AS fraud_transactions,
        SUM(CASE WHEN STATUS = 'REVIEW' THEN 1 ELSE 0 END) AS review_transactions,
        COALESCE(AVG(RISK_SCORE), 0) AS average_risk_score
    FROM FRAUDSHIELD.FRAUD_SCORES
"""


def insert_transaction(transaction: TransactionCreate) -> None:
    with ENGINE.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO FRAUDSHIELD.TRANSACTIONS
                    (TXN_ID, USER_ID, AMOUNT, CITY, MERCHANT, TXN_TIME)
                VALUES (:txn_id, :user_id, :amount, :city, :merchant, :txn_time)
            """),
            transaction.model_dump(),
        )


def get_scores(limit: int = 500) -> list[dict]:
    with ENGINE.connect() as connection:
        return [dict(row) for row in connection.execute(text(SCORES_QUERY), {"limit": limit}).mappings()]


def get_summary() -> dict:
    with ENGINE.connect() as connection:
        return dict(connection.execute(text(SUMMARY_QUERY)).mappings().one())


def ping() -> None:
    with ENGINE.connect() as connection:
        connection.execute(text("SELECT 1"))
