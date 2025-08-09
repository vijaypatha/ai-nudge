# backend/alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- CUSTOM IMPORTS FOR AI-NUDGE ---
import sys
from os.path import abspath, dirname
# Add the project root to the Python path to allow imports from common, data, etc.
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from data.database import SQLModel, DATABASE_URL
# ------------------------------------


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- CUSTOM METADATA AND URL CONFIGURATION ---

# --- THIS IS THE FIX ---
# Add imports for all of your SQLModel classes here so that Alembic's
# autogenerate can see them and compare them against the database.
from data.models.user import User
from data.models.client import Client
from data.models.message import Message, ScheduledMessage
from data.models.campaign import CampaignBriefing
from data.models.resource import Resource, ContentResource
from data.models.event import MarketEvent, GlobalMlsEvent, PipelineRun # CORRECTED IMPORT
from data.models.feedback import NegativePreference
from data.models.faq import Faq
# --- END OF FIX ---

# Point to all of your SQLModel table definitions
target_metadata = SQLModel.metadata
# Use the database URL from your application's settings
config.set_main_option('sqlalchemy.url', DATABASE_URL)
# ------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()