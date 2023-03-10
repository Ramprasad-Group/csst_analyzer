from pathlib import Path
import os

import pytest

try:
    from csst.experiment import _db
except ImportError:
    _db_option = False
else:
    _db_option = True

# don't want to ignore import errors here
if _db_option:
    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sshtunnel import SSHTunnelForwarder

if _db_option:

    @pytest.fixture(scope="module")
    def server():
        """SSH server to connect to the database through"""
        dotenv_path = Path(__file__).parent.absolute() / ".." / ".env"
        if not dotenv_path.exists():
            raise FileNotFoundError(
                ".env file must be created in the source folder with CSST_DB_USER, "
                + "CSST_DB_PASSWORD, CSST_DB_HOST, CSST_DB_PORT, CSST_DB_NAME, "
                + "SSH_TUNNEL_HOST, SSH_TUNNEL_PORT, SSH_USERNAME, and SSH_PASSWORD "
                + "set."
            )
        load_dotenv(str(dotenv_path))
        server = SSHTunnelForwarder(
            (os.environ.get("SSH_TUNNEL_HOST"), int(os.environ.get("SSH_TUNNEL_PORT"))),
            ssh_username=os.environ.get("SSH_USERNAME"),
            ssh_password=os.environ.get("SSH_PASSWORD"),
            remote_bind_address=(
                os.environ.get("CSST_DB_HOST"),
                int(os.environ.get("CSST_DB_PORT")),
            ),
        )
        server.start()
        yield server
        server.stop()

    @pytest.fixture(scope="module")
    def test_db(server):
        db_server = "postgresql+psycopg2://{}:{}@{}:{}/{}_test".format(
            os.environ.get("CSST_DB_USER"),
            os.environ.get("CSST_DB_PASSWORD"),
            os.environ.get("CSST_DB_HOST"),
            server.local_bind_port,
            os.environ.get("CSST_DB_NAME"),
        )
        engine = create_engine(db_server)
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            raise FileExistsError(
                "Database already exists. Since the database is "
                + "dropped at the end of testing, stopping the test."
            )
        return engine
