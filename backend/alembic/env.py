import os # <-- Added for database URL from environment
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- ADD THESE LINES ---
# Import your Base from database.py (adjust path if needed)
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))) # Add backend dir to path
from app.database import Base # Import your Base
# Import all your models here so Base knows about them
from app.models import Product, Source, ProductSource, PriceLog, Watchlist, ScamScore, Sale, User # Import models package or individual models
# --- END ADD ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- MODIFY THIS LINE ---
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # <-- Change None to Base.metadata
# --- END MODIFY ---

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# --- Optional: Use DATABASE_URL from environment ---
# This makes it more flexible than hardcoding in alembic.ini
db_url = os.getenv('DATABASE_URL', config.get_main_option("sqlalchemy.url"))
if db_url:
    config.set_main_option('sqlalchemy.url', db_url)
# --- End Optional ---


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    # ... (rest of the function remains the same) ...
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
    # ... (rest of the function remains the same) ...
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