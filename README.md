# FraudShield

Real-time fraud detection using Exasol SQL, a Python transaction simulator, and a Streamlit dashboard.

FraudShield receives transactions, stores them in Exasol, evaluates fraud rules in SQL, calculates risk scores, and displays live alerts. Everything runs in Docker; the host only needs Docker and the Compose plugin.

## Architecture

```text
Transaction simulator -> FastAPI backend -> Exasol transactions -> fraud_scores view -> Streamlit dashboard
```

The Compose stack contains four services:

| Service | Purpose |
| --- | --- |
| `exasol` | Database, transaction table, and fraud scoring view |
| `api` | FastAPI ingestion and analytics endpoints |
| `simulator` | Random transaction generation with probabilistic anomalies |
| `dashboard` | KPIs, charts, and live alert table |

## Prerequisites

- Docker Engine
- Docker Compose plugin (`docker compose`)
- Ports `8000`, `8501`, and `8563` available

No Python, pip, Streamlit, or Exasol client installation is required on the host.

## Quick start

From the repository root, start the application:

```bash
docker compose up --build -d
```

Open the dashboard at [http://localhost:8501](http://localhost:8501). The simulator generates random transactions every three seconds and occasionally produces anomalous activity for the Exasol rules to score.

The API is available at [http://localhost:8000/docs](http://localhost:8000/docs). It exposes transaction ingestion, health, summary, and scored transaction endpoints.

The dashboard automatically refreshes every 10 seconds and includes city risk, alert velocity, rule contribution, merchant concentration, spend anomalies, and an alert drill-down with customer history.

Alerts above a risk score of 60 can be sent to a webhook, Slack, and SMTP email by configuring the notification variables in `.env`.

Alert lifecycle state is persisted in Exasol. Operators can acknowledge or resolve alerts from the dashboard, and user profiles expose transaction count, average amount, alert count, cities, and merchants.

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment, operations, shutdown, and troubleshooting instructions.

## Fraud scoring rules

Scoring is implemented in `app/fraudshield/schema/fraud_views.sql` and runs inside Exasol:

| Rule | Score |
| --- | ---: |
| Amount exceeds five times the user's historical average | +40 |
| More than five transactions within one minute | +20 |
| Chennai transaction followed by Delhi within 15 minutes | +30 |
| Merchant has never been used by the customer | +10 |

Classification thresholds:

- `SAFE`: 0-30
- `REVIEW`: 31-60
- `FRAUD`: 61-100

## Project layout

```text
.
├── app/
│   ├── dashboard.py       # Streamlit dashboard
│   ├── Dockerfile          # Application image
│   ├── requirements.txt    # Container-only Python dependencies
│   ├── alembic.ini         # Migration configuration
│   ├── fraudshield/        # API, database, models, schema, and simulator
│   └── migrations/         # Versioned Alembic revisions
├── docker-compose.yml      # Exasol, simulator, and dashboard services
└── .env.example            # Optional environment reference
```

## Configuration

The default demo credentials and service names are defined in `docker-compose.yml`:

```text
Exasol host: exasol:8563 (inside Compose)
Exasol user: sys
Exasol password: exasol
Dashboard: http://localhost:8501
```

The simulator interval can be changed in `docker-compose.yml` through `TXN_INTERVAL_SECONDS`.

Database changes are managed with Alembic. The transaction table is defined in `app/fraudshield/models/transaction.py`, while Exasol analytics are defined in `app/fraudshield/schema/fraud_views.sql`. The API applies pending revisions with `alembic upgrade head` during startup.

Current migration chain: `0001_initial` -> `0002_alert_lifecycle`.

Migration history is append-only. Generate a new revision with `docker compose run --rm api alembic revision -m "describe the change"`; never edit a revision that has already been applied.
