CREATE OR REPLACE VIEW FRAUDSHIELD.FRAUD_SCORES AS
WITH ordered_transactions AS (
    SELECT
        t.*,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY txn_time, txn_id) AS user_txn_number,
        LAG(city) OVER (PARTITION BY user_id ORDER BY txn_time, txn_id) AS previous_city,
        LAG(txn_time) OVER (PARTITION BY user_id ORDER BY txn_time, txn_id) AS previous_txn_time,
        AVG(amount) OVER (PARTITION BY user_id ORDER BY txn_time, txn_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS rolling_average_spend,
        STDDEV_POP(amount) OVER (PARTITION BY user_id ORDER BY txn_time, txn_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS rolling_spend_volatility,
        PERCENT_RANK() OVER (PARTITION BY user_id ORDER BY amount) AS user_amount_percentile,
        COUNT(*) OVER (PARTITION BY user_id ORDER BY txn_time, txn_id ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS six_transaction_window,
        COUNT(*) OVER (PARTITION BY user_id ORDER BY txn_time RANGE BETWEEN INTERVAL '1' MINUTE PRECEDING AND CURRENT ROW) AS transactions_last_minute,
        ROW_NUMBER() OVER (PARTITION BY user_id, merchant ORDER BY txn_time, txn_id) - 1 AS prior_merchant_uses
    FROM FRAUDSHIELD.TRANSACTIONS t
), features AS (
    SELECT o.*,
        COALESCE(o.rolling_average_spend, 0) AS user_average_spend,
        COALESCE(o.rolling_spend_volatility, 0) AS user_spend_volatility,
        0 AS prior_city_count
    FROM ordered_transactions o
), scored AS (
    SELECT f.*,
        CASE WHEN user_average_spend > 0 AND amount > 5 * user_average_spend THEN 40 ELSE 0 END AS high_amount_score,
        CASE WHEN transactions_last_minute > 5 THEN 20 ELSE 0 END AS rapid_score,
        CASE WHEN previous_city = 'Chennai' AND city = 'Delhi' AND previous_txn_time >= ADD_MINUTES(txn_time, -15) THEN 30 ELSE 0 END AS impossible_travel_score,
        CASE WHEN prior_merchant_uses = 0 THEN 10 ELSE 0 END AS new_merchant_score,
        CASE WHEN user_spend_volatility > 0 THEN (amount - user_average_spend) / user_spend_volatility ELSE 0 END AS spend_z_score
    FROM features f
), final_scores AS (
    SELECT s.*, high_amount_score + rapid_score + impossible_travel_score + new_merchant_score AS risk_score
    FROM scored s
)
SELECT final_scores.*,
    CASE WHEN final_scores.risk_score >= 61 THEN 'FRAUD' WHEN final_scores.risk_score >= 31 THEN 'REVIEW' ELSE 'SAFE' END AS status,
    RTRIM(CASE WHEN high_amount_score > 0 THEN 'High amount; ' ELSE '' END || CASE WHEN rapid_score > 0 THEN 'Rapid activity; ' ELSE '' END || CASE WHEN impossible_travel_score > 0 THEN 'Impossible travel; ' ELSE '' END || CASE WHEN new_merchant_score > 0 THEN 'New merchant; ' ELSE '' END, '; ') AS alert_reasons,
    COALESCE(alerts.lifecycle_status, CASE WHEN risk_score >= 31 THEN 'NEW' ELSE 'NONE' END) AS lifecycle_status,
    alerts.updated_at AS lifecycle_updated_at,
    alerts.acknowledged_by,
    alerts.resolved_at
FROM final_scores
LEFT JOIN FRAUDSHIELD.FRAUD_ALERTS alerts ON alerts.txn_id = final_scores.txn_id;
