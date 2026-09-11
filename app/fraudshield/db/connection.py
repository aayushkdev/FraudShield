import os
import time

from alembic import command
from alembic.config import Config
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

DSN = os.getenv("EXASOL_DSN", "localhost:8563")
USER = os.getenv("EXASOL_USER", "sys")
PASSWORD = os.getenv("EXASOL_PASSWORD", "exasol")
ALEMBIC_INI = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
HOST, _, PORT = DSN.partition(":")

ENGINE = create_engine(
    URL.create(
        "exa+pyexasol",
        username=USER,
        password=PASSWORD,
        host=HOST,
        port=int(PORT or 8563),
    ),
    pool_pre_ping=True,
)


def connect():
    return ENGINE.connect()


def initialize_database(retries=30):
    last_error = None
    for _ in range(retries):
        try:
            command.upgrade(Config(ALEMBIC_INI), "head")
            return
        except Exception as error:
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"Could not initialize Exasol after {retries} attempts: {last_error}")


def query_dataframe(query):
    with connect() as connection:
        return pd.read_sql_query(text(query), connection)
