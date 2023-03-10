import os

import pytest

# test if db and db_dev dependencies installed
try:
    from pinrex import db
    from sqlalchemy_utils import database_exists, create_database
except ImportError:
    _db_option = False
else:
    _db_option = True


def test_if_dependencies_installed():
    if not _db_option:
        pytest.exit(
            reason=(
                "This test is only run if the optional database and database dev "
                + "dependencies are installed. Use `poetry install --with db,db_dev` "
                + "to install them."
            ),
            returncode=5,
        )


def test_connection(ssh_connection):
    print(f"port is {os.environ.get('SSH_TUNNEL_HOST')}")
