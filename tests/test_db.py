import os

import pytest

# test if db and db_dev dependencies installed
# db dependency
db = pytest.importorskip(
    "pinrex.db",
    reason=(
        "This test is only run if the optional database and database dev "
        + "dependencies are installed. Use `poetry install --with db,db_dev` "
        + "to install them."
    ),
)
# db_dev dependency
pytest.importorskip(
    "sqlalchemy_utils",
    reason=(
        "This test is only run if the optional database and database dev "
        + "dependencies are installed. Use `poetry install --with db,db_dev` "
        + "to install them."
    ),
)

from pinrex.db.models.polymer import Polymer

def test_connection(session):
    assert session.query(Polymer).first().smiles == "[*]SCCCC([*])=O"
