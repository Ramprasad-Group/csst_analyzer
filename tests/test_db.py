import os

import pytest

# test if db and db_dev dependencies installed
# db dependency
db = pytest.importorskip(
    "csst.experiment._db",
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
from pinrex.db.models.csst import (
    CSSTReactor,
    CSSTProperty,
    CSSTExperiment,
    CSSTTemperatureProgram,
)

from .fixtures.data import csste_1014


def test_connection(session):
    assert session.query(Polymer).first().smiles == "[*]CCO[*]"


@pytest.mark.slow
def test_add_experiment(session, csste_1014):
    db.add_experiment(csste_1014, session)
    assert (
        session.query(CSSTReactor)
        .filter(CSSTReactor.csst_experiment_id != 10000)
        .count()
        == 3
    )
    assert session.query(CSSTProperty).count() == 6
    assert (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment=csste_1014.start_of_experiment)
        .count()
    ) == 1
    assert (
        session.query(CSSTTemperatureProgram)
        .filter(CSSTTemperatureProgram.hash == csste_1014.temperature_program.hash())
        .count()
    ) == 1
