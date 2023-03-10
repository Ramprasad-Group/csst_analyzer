import pytest

try:
    from pinrex import db
    from sqlalchemy_utils import database_exists, create_database
except ImportError:
    _db_option = False
else:
    _db_option = True

if _db_option:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session

def test_database_connection():
    if not _db_option:
        pytest.exit(
            reason=(
                "This test is only run if the optional database and database dev "
                + "dependencies are installed. Use `poetry install --with db,db_dev` "
                + "to install them."
            ),
            returncode=5
        )
    pass
