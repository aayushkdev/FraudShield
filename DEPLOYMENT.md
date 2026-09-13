# FraudShield Deployment and Run Guide

This guide covers deployment and operation of the Docker Compose stack.

## Requirements

- Docker Engine
- Docker Compose plugin (`docker compose`)
- Ports `8000`, `8501`, and `8563` available
- At least 4 GB of available memory for the Exasol container

No host-side Python, pip, Streamlit, or Exasol driver installation is required.

## Start the application

Run commands from the repository root:

```bash
docker compose up --build -d
```

The first startup downloads the large Exasol database image and may take several minutes. If the download is interrupted, run the same command again; Docker reuses completed image layers.

The stack contains:

| Service | Purpose |
| --- | --- |
| `exasol` | Database, transaction storage, and SQL scoring view |
| `api` | FastAPI backend on port `8000` |
| `simulator` | Random transaction generation with probabilistic anomalies |
| `dashboard` | Streamlit dashboard on port `8501` |

Open [http://localhost:8501](http://localhost:8501) after startup.
Open the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## API endpoints

```text
GET  /health
POST /api/v1/transactions
GET  /api/v1/analytics/scores
GET  /api/v1/analytics/summary
```

The simulator publishes validated transaction payloads to the API. The API service owns ingestion and reads analytics from Exasol; the dashboard does not connect to the database directly.

The dashboard refreshes automatically every 10 seconds. Select an alert in the drill-down panel to inspect its triggered rules, user history, risk score, and spend percentile.

## Verify deployment

Check service status:

```bash
docker compose ps
```

View all service logs:

```bash
docker compose logs -f
```

View individual services:

```bash
docker compose logs -f exasol
docker compose logs -f api
docker compose logs -f simulator
docker compose logs -f dashboard
```

Exasol must become healthy before the API can connect. The simulator then publishes random transactions every three seconds, with occasional anomalous amounts and new merchants.

## Operate the stack

Rebuild after changing application code or dependencies:

```bash
docker compose up --build -d
```

Restart without rebuilding:

```bash
docker compose restart
```

Apply database migrations manually when needed:

```bash
docker compose run --rm api alembic upgrade head
```

The API runs `alembic upgrade head` automatically during startup, so this command is normally only useful for deployment diagnostics.

Stop services while preserving Exasol data:

```bash
docker compose down
```

Stop services and delete the persisted demo database:

```bash
docker compose down -v
```

Use `down -v` when you need a clean demo database. The simulator resumes generating random traffic on the next startup.

## Configuration

Default values in `docker-compose.yml`:

```text
Exasol host inside Compose: exasol:8563
Exasol user: sys
Exasol password: exasol
Dashboard: http://localhost:8501
Simulator interval: 3 seconds
```

Change `TXN_INTERVAL_SECONDS` in the `simulator` service to change the transaction generation rate.

## Troubleshooting

### Interrupted image download

Run the startup command again:

```bash
docker compose up --build -d
```

### Dashboard cannot connect to the API

Check the API and database logs:

```bash
docker compose ps
docker compose logs exasol
docker compose logs api
```

After the API is healthy, restart the application services:

```bash
docker compose restart simulator dashboard
```

### Port already in use

Stop the process using port `8501` or `8563`, or change the host-side port mapping in `docker-compose.yml`. Keep the internal database address as `exasol:8563`.

## Key files

- `docker-compose.yml`: services, healthcheck, networking, and persistence.
- `app/Dockerfile`: application image definition.
- `app/requirements.txt`: container-only dependencies.
- `app/alembic.ini`: Alembic configuration.
- `app/migrations/`: versioned database revisions.
- `app/fraudshield/schema/`: API schemas and Exasol analytics SQL.
- `app/fraudshield/models/`: SQLAlchemy transaction models.
- `app/fraudshield/main.py`: FastAPI application.
- `app/fraudshield/api/`: versioned HTTP routes.
- `app/fraudshield/db/`: SQLAlchemy engine and database query functions.
- `app/fraudshield/services/`: application use cases.
- `app/fraudshield/simulator.py`: random transaction generator.
- `app/dashboard.py`: Streamlit dashboard.
