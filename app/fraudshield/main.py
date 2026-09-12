from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from fraudshield.api.routes import router
from fraudshield.db import initialize_database, ping


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="FraudShield API",
    version="1.0.0",
    description="Transaction ingestion and Exasol-powered fraud analytics API.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
def health():
    try:
        ping()
        return {"status": "ok", "database": "ok"}
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {error}") from error
