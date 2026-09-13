from fastapi import FastAPI, HTTPException

from fraudshield.api.routes import router
from fraudshield.db import ping


app = FastAPI(
    title="FraudShield API",
    version="1.0.0",
    description="Transaction ingestion and Exasol-powered fraud analytics API.",
)
app.include_router(router)


@app.get("/health")
def health():
    try:
        ping()
        return {"status": "ok", "database": "ok"}
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {error}") from error
