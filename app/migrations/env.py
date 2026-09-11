from logging.config import fileConfig

from alembic import context

from fraudshield.db.connection import ENGINE
from fraudshield.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=str(ENGINE.url),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with ENGINE.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="FRAUDSHIELD_ALEMBIC_VERSION",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
