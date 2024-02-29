import os
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from dotenv import load_dotenv

from alembic import context

from csst.db import Base

dotenv_path = Path(__file__).parent.absolute() / ".." / ".env"
if not dotenv_path.exists():
    raise FileNotFoundError(
        ".env file must be created in the source folder with CSST_DB_USER, "
        + "CSST_DB_PASSWORD, CSST_DB_HOST, CSST_DB_PORT, CSST_DB_NAME, "
        + "CSST_DB_SSH_TUNNEL_HOST, CSST_DB_SSH_TUNNEL_PORT, CSST_DB_SSH_USERNAME, "
        + "and CSST_DB_SSH_PASSWORD set."
    )
load_dotenv(str(dotenv_path))
_remote_access = os.environ.get("CSST_DB_IS_REMOTE") == "true"

try:
    from sshtunnel import SSHTunnelForwarder
except ImportError:
    if _remote_access:
        raise ValueError(
            "CSST_DB_IS_REMOTE is set to true, but sshtunnel was not installed. "
            + "Try running `poetry install --extras remote` to install it."
        )

if _remote_access:
    server = SSHTunnelForwarder(
        (
            os.environ.get("CSST_DB_SSH_TUNNEL_HOST"),
            int(os.environ.get("CSST_DB_SSH_TUNNEL_PORT")),
        ),
        ssh_username=os.environ.get("CSST_DB_SSH_USERNAME"),
        ssh_password=os.environ.get("CSST_DB_SSH_PASSWORD"),
        remote_bind_address=(
            os.environ.get("CSST_DB_HOST"),
            int(os.environ.get("CSST_DB_PORT")),
        ),
    )
    server.start()
    port = server.local_bind_port
else:
    port = os.environ.get("CSST_DB_PORT")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = "postgresql+psycopg://{}:{}@{}:{}/{}".format(
        os.environ.get("CSST_DB_USER"),
        os.environ.get("CSST_DB_PASSWORD"),
        os.environ.get("CSST_DB_HOST"),
        port,
        os.environ.get("CSST_DB_NAME"),
    )
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
    connectable = create_engine(
        "postgresql+psycopg://{}:{}@{}:{}/{}".format(
            os.environ.get("CSST_DB_USER"),
            os.environ.get("CSST_DB_PASSWORD"),
            os.environ.get("CSST_DB_HOST"),
            port,
            os.environ.get("CSST_DB_NAME"),
        )
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

if _remote_access:
    server.stop()
