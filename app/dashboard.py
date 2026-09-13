import os

import pandas as pd
import httpx
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BACKEND_URL = os.getenv("BACKEND_URL", "http://api:8000")
px.defaults.template = "plotly_dark"
st.set_page_config(page_title="FraudShield", page_icon="FS", layout="wide")
st_autorefresh(interval=10000, limit=None, key="fraudshield-refresh")

NUMERIC_COLUMNS = [
    "TXN_ID", "AMOUNT", "RISK_SCORE", "USER_AVERAGE_SPEND", "USER_SPEND_VOLATILITY",
    "SPEND_Z_SCORE", "USER_AMOUNT_PERCENTILE", "TRANSACTIONS_LAST_MINUTE",
    "SIX_TRANSACTION_WINDOW", "PRIOR_MERCHANT_USES", "PRIOR_CITY_COUNT",
    "HIGH_AMOUNT_SCORE", "RAPID_SCORE", "IMPOSSIBLE_TRAVEL_SCORE", "NEW_MERCHANT_SCORE",
]

st.markdown("""
<style>
    .stApp { background: #101820; color: #eef5f2; }
    [data-testid="stHeader"] { background: #101820; }
    [data-testid="stMetric"] { background: #17252f; border: 1px solid #2d4652; padding: 16px; border-radius: 8px; }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { color: #eef5f2; }
    [data-testid="stDataFrame"] { border: 1px solid #2d4652; }
    .stButton > button { background: #1e8f78; color: #ffffff; border: 0; }
    .stButton > button:hover { background: #25ad91; color: #ffffff; }
    .stSelectbox label, .stMarkdown, .stCaption, h1, h2, h3, p { color: #eef5f2 !important; }
    .hero { padding: 24px 0 12px; }
    .hero h1 { color: #8ee3c5; margin-bottom: 4px; }
    .hero p { color: #b6c9c4; font-size: 1.05rem; }
    [data-baseweb="select"] > div { background: #17252f; color: #eef5f2; border-color: #2d4652; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>FraudShield</h1><p>Real-time transaction intelligence powered by Exasol SQL.</p></div>', unsafe_allow_html=True)
st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.button("Refresh data"):
    st.rerun()

try:
    response = httpx.get(f"{BACKEND_URL}/api/v1/analytics/scores", params={"limit": 500}, timeout=10)
    response.raise_for_status()
    data = pd.DataFrame(response.json())
    data.columns = [str(column).upper() for column in data.columns]
    for column in NUMERIC_COLUMNS:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
except Exception as error:
    st.error(f"Waiting for the FraudShield API: {error}")
    st.stop()

if data.empty:
    st.info("Waiting for the simulator to publish transactions...")
    st.stop()

fraud_count = int((data["STATUS"] == "FRAUD").sum())
review_count = int((data["STATUS"] == "REVIEW").sum())
transaction_count = len(data)
fraud_percent = fraud_count / transaction_count * 100
data["TXN_TIME"] = pd.to_datetime(data["TXN_TIME"])

metrics = st.columns(4)
metrics[0].metric("Total transactions", f"{transaction_count:,}")
metrics[1].metric("Fraud transactions", f"{fraud_count:,}")
metrics[2].metric("Needs review", f"{review_count:,}")
metrics[3].metric("Fraud percentage", f"{fraud_percent:.1f}%")

st.divider()
left, right = st.columns(2)
with left:
    city_data = data.groupby("CITY", as_index=False).agg(
        transactions=("TXN_ID", "count"),
        alerts=("STATUS", lambda values: (values != "SAFE").sum()),
        average_score=("RISK_SCORE", "mean"),
    )
    city_data["alert_rate"] = city_data["alerts"] / city_data["transactions"] * 100
    st.subheader("Risk by city")
    st.plotly_chart(
        px.bar(city_data.sort_values("alert_rate"), x="alert_rate", y="CITY", orientation="h", color="average_score", color_continuous_scale="Teal", labels={"alert_rate": "Alert rate (%)", "CITY": ""}),
        use_container_width=True,
    )
with right:
    st.subheader("Alert velocity")
    trend = data.set_index("TXN_TIME").resample("5min").agg(
        transactions=("TXN_ID", "count"),
        alerts=("STATUS", lambda values: (values != "SAFE").sum()),
        average_score=("RISK_SCORE", "mean"),
    ).reset_index()
    trend_long = trend.melt("TXN_TIME", value_vars=["transactions", "alerts"], var_name="metric", value_name="count")
    st.plotly_chart(px.line(trend_long, x="TXN_TIME", y="count", color="metric", markers=True, labels={"count": "Transactions", "TXN_TIME": ""}), use_container_width=True)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Which rules drive risk?")
    rule_scores = data[["HIGH_AMOUNT_SCORE", "RAPID_SCORE", "IMPOSSIBLE_TRAVEL_SCORE", "NEW_MERCHANT_SCORE"]].sum().reset_index()
    rule_scores.columns = ["rule", "points"]
    rule_scores["rule"] = rule_scores["rule"].str.replace("_SCORE", "", regex=False).str.replace("_", " ").str.title()
    st.plotly_chart(px.bar(rule_scores.sort_values("points"), x="points", y="rule", orientation="h", color="points", color_continuous_scale="Sunset", labels={"rule": "", "points": "Risk points"}), use_container_width=True)
with right:
    st.subheader("Merchant concentration")
    merchant_data = data.groupby("MERCHANT", as_index=False).agg(
        transactions=("TXN_ID", "count"),
        alerts=("STATUS", lambda values: (values != "SAFE").sum()),
        average_score=("RISK_SCORE", "mean"),
    )
    merchant_data["alert_rate"] = merchant_data["alerts"] / merchant_data["transactions"] * 100
    st.plotly_chart(px.scatter(merchant_data, x="transactions", y="alert_rate", size="average_score", color="average_score", hover_name="MERCHANT", color_continuous_scale="Teal", labels={"transactions": "Transactions", "alert_rate": "Alert rate (%)"}), use_container_width=True)

st.subheader("Spend anomaly map")
st.plotly_chart(
    px.scatter(
        data,
        x="USER_AVERAGE_SPEND",
        y="AMOUNT",
        color="STATUS",
        size="RISK_SCORE",
        hover_data=["USER_ID", "MERCHANT", "SPEND_Z_SCORE", "USER_AMOUNT_PERCENTILE"],
        color_discrete_map={"FRAUD": "#d1495b", "REVIEW": "#f0a202", "SAFE": "#2a9d8f"},
        labels={"USER_AVERAGE_SPEND": "Historical average spend", "AMOUNT": "Transaction amount"},
    ),
    use_container_width=True,
)

st.subheader("Live alert table")
alerts = data[data["STATUS"] != "SAFE"].copy()
if alerts.empty:
    st.success("No suspicious transactions detected.")
else:
    st.dataframe(
        alerts[["TXN_ID", "USER_ID", "AMOUNT", "CITY", "MERCHANT", "RISK_SCORE", "STATUS", "LIFECYCLE_STATUS", "ALERT_REASONS", "TXN_TIME"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "AMOUNT": st.column_config.NumberColumn("Amount", format="₹%.2f"),
            "RISK_SCORE": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100),
        },
    )

    st.subheader("Alert drill-down")
    alert_ids = alerts["TXN_ID"].astype(str).tolist()
    selected_id = st.selectbox("Select an alert", alert_ids, label_visibility="collapsed")
    selected_alert = alerts[alerts["TXN_ID"].astype(str) == selected_id].iloc[0]
    selected_txn_id = int(selected_alert["TXN_ID"])
    lifecycle = str(selected_alert["LIFECYCLE_STATUS"])
    lifecycle_columns = st.columns(2)
    if lifecycle == "NEW" and lifecycle_columns[0].button("Acknowledge alert"):
        try:
            response = httpx.patch(f"{BACKEND_URL}/api/v1/alerts/{selected_txn_id}", json={"status": "ACKNOWLEDGED"}, timeout=10)
            response.raise_for_status()
            st.rerun()
        except httpx.HTTPError as error:
            st.error(f"Could not acknowledge alert: {error}")
    if lifecycle in {"NEW", "ACKNOWLEDGED"} and lifecycle_columns[1].button("Resolve alert"):
        try:
            response = httpx.patch(f"{BACKEND_URL}/api/v1/alerts/{selected_txn_id}", json={"status": "RESOLVED"}, timeout=10)
            response.raise_for_status()
            st.rerun()
        except httpx.HTTPError as error:
            st.error(f"Could not resolve alert: {error}")
    detail_columns = st.columns(4)
    detail_columns[0].metric("User", str(selected_alert["USER_ID"]))
    detail_columns[1].metric("Risk score", int(selected_alert["RISK_SCORE"]))
    detail_columns[2].metric("Rule triggers", selected_alert["ALERT_REASONS"] or "None")
    detail_columns[3].metric("Spend percentile", f"{float(selected_alert['USER_AMOUNT_PERCENTILE']) * 100:.0f}%")
    user_history = data[data["USER_ID"] == selected_alert["USER_ID"]].copy()
    detail_columns = st.columns(3)
    detail_columns[0].metric("Average spend", f"₹{user_history['AMOUNT'].mean():,.0f}")
    detail_columns[1].metric("Previous cities", user_history["CITY"].nunique())
    detail_columns[2].metric("Merchant history", user_history["MERCHANT"].nunique())
    st.dataframe(
        user_history[
            ["TXN_TIME", "AMOUNT", "CITY", "MERCHANT", "RISK_SCORE", "STATUS", "ALERT_REASONS"]
        ].sort_values("TXN_TIME", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("User risk profiles")
try:
    profiles_response = httpx.get(f"{BACKEND_URL}/api/v1/analytics/profiles", timeout=10)
    profiles_response.raise_for_status()
    profiles = pd.DataFrame(profiles_response.json())
    profiles.columns = [str(column).upper() for column in profiles.columns]
    for column in ["TOTAL_TRANSACTIONS", "AVERAGE_AMOUNT", "RISK_SCORE", "ALERT_COUNT", "UNIQUE_CITIES", "UNIQUE_MERCHANTS"]:
        if column in profiles:
            profiles[column] = pd.to_numeric(profiles[column], errors="coerce")
    st.dataframe(profiles, use_container_width=True, hide_index=True)
except Exception as error:
    st.warning(f"Profiles unavailable: {error}")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Alerts by hour")
    hourly = data.assign(hour=data["TXN_TIME"].dt.hour).groupby("hour", as_index=False).agg(
        alerts=("STATUS", lambda values: (values != "SAFE").sum()),
        transactions=("TXN_ID", "count"),
    )
    st.plotly_chart(px.bar(hourly, x="hour", y="alerts", labels={"hour": "Hour of day", "alerts": "Alerts"}), use_container_width=True)
with right:
    st.subheader("Weekday vs weekend")
    weekday = data.assign(period=data["TXN_TIME"].dt.dayofweek.map(lambda day: "Weekend" if day >= 5 else "Weekday"))
    weekday = weekday.groupby("period", as_index=False).agg(alerts=("STATUS", lambda values: (values != "SAFE").sum()), transactions=("TXN_ID", "count"))
    weekday["alert_rate"] = weekday["alerts"] / weekday["transactions"] * 100
    st.plotly_chart(px.bar(weekday, x="period", y="alert_rate", color="period", labels={"alert_rate": "Alert rate (%)"}), use_container_width=True)

st.subheader("Merchant intelligence")
merchant_detail = data.groupby("MERCHANT", as_index=False).agg(
    transactions=("TXN_ID", "count"),
    alerts=("STATUS", lambda values: (values != "SAFE").sum()),
    new_merchant_events=("NEW_MERCHANT_SCORE", lambda values: (values > 0).sum()),
    average_amount=("AMOUNT", "mean"),
    average_risk=("RISK_SCORE", "mean"),
)
merchant_detail["alert_rate"] = merchant_detail["alerts"] / merchant_detail["transactions"] * 100
st.dataframe(merchant_detail.sort_values("alert_rate", ascending=False), use_container_width=True, hide_index=True)

st.caption("Refresh the page to pull the latest scores from Exasol.")
