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
from pinrex.db.models.csst import CSSTExperiment, CSSTTemperatureProgram

from .fixtures.data import csste_1014, manual_1014

def test_connection(session):
    assert session.query(Polymer).first().smiles == "[*]CCO[*]"

def test__add_experiment(session, csste_1014):
    db._add_experiment(csste_1014, session)
    experiment = (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment = csste_1014.start_of_experiment)
        .first()
    )
    assert experiment.version == csste_1014.version
    assert experiment.experiment_details == csste_1014.experiment_details
    assert experiment.experiment_number == csste_1014.experiment_number
    assert experiment.experimenter == csste_1014.experimenter
    assert experiment.project == csste_1014.project
    assert experiment.lab_journal == csste_1014.lab_journal
    assert experiment.description == "\n".join(csste_1014.description)
    assert experiment.start_of_experiment == csste_1014.start_of_experiment
    db._add_experiment(csste_1014, session)
    assert (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment = csste_1014.start_of_experiment)
        .count()
    ) == 1

def test__add_temperature_program(session, manual_1014):
    db._add_temperature_program(manual_1014, session)
    temp_program = (
        session.query(CSSTTemperatureProgram)
        .filter(CSSTTemperatureProgram.hash == manual_1014.temperature_program.hash())
        .first()
    )
    assert temp_program.block == manual_1014.temperature_program.block
    assert temp_program.solvent_tune == [step.dict() for step in manual_1014.temperature_program.solvent_tune]
    assert temp_program.sample_load == [step.dict() for step in manual_1014.temperature_program.sample_load]
    assert temp_program.experiment == [step.dict() for step in manual_1014.temperature_program.experiment]
    db._add_temperature_program(manual_1014, session)
    assert (
        session.query(CSSTTemperatureProgram)
        .filter(CSSTTemperatureProgram.hash == manual_1014.temperature_program.hash())
        .count()
    ) == 1
