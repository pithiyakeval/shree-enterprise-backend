
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import engine_from_config

from alembic import context

# Import your database settings
from app.config import settings

# Import Base and models
from app.database import Base
from app import models  # IMPORTANT: loads all models


config = context.config

# Inject database URL dynamically
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL_SYNC.replace("%","%%")
)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic uses to detect tables
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()