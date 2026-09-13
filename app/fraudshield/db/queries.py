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

DETAIL_QUERY = "SELECT * FROM FRAUDSHIELD.FRAUD_SCORES WHERE TXN_ID = :txn_id"
PROFILE_QUERY = """
    SELECT USER_ID, COUNT(*) AS total_transactions, AVG(AMOUNT) AS average_amount,
        MAX(RISK_SCORE) AS risk_score, SUM(CASE WHEN STATUS <> 'SAFE' THEN 1 ELSE 0 END) AS alert_count,
        COUNT(DISTINCT CITY) AS unique_cities, COUNT(DISTINCT MERCHANT) AS unique_merchants
    FROM FRAUDSHIELD.FRAUD_SCORES
    GROUP BY USER_ID ORDER BY risk_score DESC
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


def get_transaction(txn_id: int) -> dict | None:
    with ENGINE.connect() as connection:
        row = connection.execute(text(DETAIL_QUERY), {"txn_id": txn_id}).mappings().first()
        return dict(row) if row else None


def get_profiles() -> list[dict]:
    with ENGINE.connect() as connection:
        return [dict(row) for row in connection.execute(text(PROFILE_QUERY)).mappings()]


def update_alert(txn_id: int, lifecycle_status: str, actor: str) -> None:
    with ENGINE.begin() as connection:
        connection.execute(text("""
            MERGE INTO FRAUDSHIELD.FRAUD_ALERTS target
            USING (SELECT :txn_id AS txn_id) source ON target.txn_id = source.txn_id
            WHEN MATCHED THEN UPDATE SET lifecycle_status = :status, updated_at = CURRENT_TIMESTAMP, acknowledged_by = :actor,
                resolved_at = CASE WHEN :status = 'RESOLVED' THEN CURRENT_TIMESTAMP ELSE resolved_at END
            WHEN NOT MATCHED THEN INSERT (txn_id, lifecycle_status, updated_at, acknowledged_by, resolved_at)
                VALUES (:txn_id, :status, CURRENT_TIMESTAMP, :actor, CASE WHEN :status = 'RESOLVED' THEN CURRENT_TIMESTAMP ELSE NULL END)
        """), {"txn_id": txn_id, "status": lifecycle_status, "actor": actor})


def get_summary() -> dict:
    with ENGINE.connect() as connection:
        return dict(connection.execute(text(SUMMARY_QUERY)).mappings().one())


def ping() -> None:
    with ENGINE.connect() as connection:
        connection.execute(text("SELECT 1"))
