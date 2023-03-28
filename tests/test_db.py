import os

import pytest
import numpy as np

# test if db and db_dev dependencies installed
# db dependency
db = pytest.importorskip(
    "csst.db",
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

from csst.experiment import Experiment
from csst.experiment.models import PropertyValue
from .fixtures.data import csste_1014


def test_connection(session):
    assert session.query(Polymer).first().smiles == "[*]CCO[*]"


@pytest.mark.slow
def test_add_experiment(session, csste_1014):
    old_num_props = session.query(CSSTProperty).count()
    db.add_experiment(csste_1014, session)
    assert (
        session.query(CSSTReactor)
        .filter(CSSTReactor.csst_experiment_id < 10000)
        .count()
        == 3
    )
    assert session.query(CSSTProperty).count() == 6 + old_num_props
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


@pytest.mark.slow
def test_get_experiment(session, csste_1014):
    db.add_experiment(csste_1014, session)
    exps = db.get_experiments_from_experiment_details(csste_1014, session)
    exp = exps[0]
    assert csste_1014.file_name == exp.file_name
    assert csste_1014.experiment_details == exp.experiment_details
    assert csste_1014.experiment_number == exp.experiment_number
    assert csste_1014.experimenter == exp.experimenter
    assert csste_1014.project == exp.project
    assert csste_1014.lab_journal == exp.lab_journal
    assert csste_1014.description == exp.description
    assert csste_1014.start_of_experiment == exp.start_of_experiment

    assert csste_1014.temperature_program.block == exp.temperature_program.block
    assert csste_1014.bottom_stir_rate == exp.bottom_stir_rate
    assert len(exp.temperature_program.solvent_tune) == len(
        csste_1014.temperature_program.solvent_tune
    )
    for i in range(len(csste_1014.temperature_program.solvent_tune)):
        assert (
            exp.temperature_program.solvent_tune[i]
            == csste_1014.temperature_program.solvent_tune[i]
        )

    assert len(exp.temperature_program.sample_load) == len(
        csste_1014.temperature_program.sample_load
    )
    for i in range(len(csste_1014.temperature_program.sample_load)):
        assert (
            exp.temperature_program.sample_load[i]
            == csste_1014.temperature_program.sample_load[i]
        )

    assert len(exp.temperature_program.experiment) == len(
        csste_1014.temperature_program.experiment
    )
    for i in range(len(csste_1014.temperature_program.experiment)):
        assert (
            exp.temperature_program.experiment[i]
            == csste_1014.temperature_program.experiment[i]
        )

    assert exp.temperature_program == csste_1014.temperature_program

    datablock_size = 32337 - 38
    assert len(exp.time_since_experiment_start.values) == datablock_size

    assert exp.set_temperature.unit == "°C"
    assert len(exp.set_temperature.values) == datablock_size

    assert exp.actual_temperature.unit == "°C"
    assert len(exp.actual_temperature.values) == datablock_size
    assert np.array_equal(exp.set_temperature.values, csste_1014.set_temperature.values)
    assert np.array_equal(
        exp.actual_temperature.values, csste_1014.actual_temperature.values
    )

    assert np.array_equal(exp.stir_rates.values, csste_1014.stir_rates.values)

    assert exp.bottom_stir_rate.value == csste_1014.bottom_stir_rate.value

    assert exp.stir_rates.unit == "rpm"
    assert len(exp.stir_rates.values) == datablock_size

    assert len(exp.reactors) == 3
    for i in range(len(exp.reactors)):
        reactor = exp.reactors[i]
        assert len(reactor.transmission.values) == datablock_size
        assert np.array_equal(
            reactor.transmission.values, csste_1014.reactors[i].transmission.values
        )
        assert reactor.solvent == "methanol"
        if i == 0:
            assert reactor.polymer == "PEG"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.11, unit="mg/ml"
            )
        if i == 1:
            assert reactor.polymer == "PEG"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.19, unit="mg/ml"
            )
        if i == 2:
            assert reactor.polymer == "PVP"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.10, unit="mg/ml"
            )

    exp.reactors[0].experiment.actual_temperature.values[0] = 10000
    assert exp.reactors[1].experiment.actual_temperature.values[0] == 10000
    exp.reactors[0].experiment.actual_temperature.values[0] = 1
    assert exp.reactors[1].experiment.actual_temperature.values[0] == 1


@pytest.mark.slow
def test_load_from_db(session, csste_1014):
    exps = db.load_from_db(
        Session=session, start_of_experiment=csste_1014.start_of_experiment
    )
    assert len(exps) == 0
    db.add_experiment(csste_1014, session)
    exps = db.load_from_db(
        Session=session, start_of_experiment=csste_1014.start_of_experiment
    )
    exp = exps[0]
    assert csste_1014.file_name == exp.file_name
    assert csste_1014.experiment_details == exp.experiment_details
    assert csste_1014.experiment_number == exp.experiment_number
    assert csste_1014.experimenter == exp.experimenter
    assert csste_1014.project == exp.project
    assert csste_1014.lab_journal == exp.lab_journal
    assert csste_1014.description == exp.description
    assert csste_1014.start_of_experiment == exp.start_of_experiment

    assert csste_1014.temperature_program.block == exp.temperature_program.block
    assert csste_1014.bottom_stir_rate == exp.bottom_stir_rate
    assert len(exp.temperature_program.solvent_tune) == len(
        csste_1014.temperature_program.solvent_tune
    )
    for i in range(len(csste_1014.temperature_program.solvent_tune)):
        assert (
            exp.temperature_program.solvent_tune[i]
            == csste_1014.temperature_program.solvent_tune[i]
        )

    assert len(exp.temperature_program.sample_load) == len(
        csste_1014.temperature_program.sample_load
    )
    for i in range(len(csste_1014.temperature_program.sample_load)):
        assert (
            exp.temperature_program.sample_load[i]
            == csste_1014.temperature_program.sample_load[i]
        )

    assert len(exp.temperature_program.experiment) == len(
        csste_1014.temperature_program.experiment
    )
    for i in range(len(csste_1014.temperature_program.experiment)):
        assert (
            exp.temperature_program.experiment[i]
            == csste_1014.temperature_program.experiment[i]
        )

    assert exp.temperature_program == csste_1014.temperature_program

    datablock_size = 32337 - 38
    assert len(exp.time_since_experiment_start.values) == datablock_size

    assert exp.set_temperature.unit == "°C"
    assert len(exp.set_temperature.values) == datablock_size

    assert exp.actual_temperature.unit == "°C"
    assert len(exp.actual_temperature.values) == datablock_size
    assert np.array_equal(exp.set_temperature.values, csste_1014.set_temperature.values)
    assert np.array_equal(
        exp.actual_temperature.values, csste_1014.actual_temperature.values
    )

    assert np.array_equal(exp.stir_rates.values, csste_1014.stir_rates.values)

    assert exp.bottom_stir_rate.value == csste_1014.bottom_stir_rate.value

    assert exp.stir_rates.unit == "rpm"
    assert len(exp.stir_rates.values) == datablock_size

    assert len(exp.reactors) == 3
    for i in range(len(exp.reactors)):
        reactor = exp.reactors[i]
        assert len(reactor.transmission.values) == datablock_size
        assert np.array_equal(
            reactor.transmission.values, csste_1014.reactors[i].transmission.values
        )
        assert reactor.solvent == "methanol"
        if i == 0:
            assert reactor.polymer == "PEG"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.11, unit="mg/ml"
            )
        if i == 1:
            assert reactor.polymer == "PEG"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.19, unit="mg/ml"
            )
        if i == 2:
            assert reactor.polymer == "PVP"
            assert reactor.conc == PropertyValue(
                name="concentration", value=5.10, unit="mg/ml"
            )

    exp.reactors[0].experiment.actual_temperature.values[0] = 10000
    assert exp.reactors[1].experiment.actual_temperature.values[0] == 10000
    exp.reactors[0].experiment.actual_temperature.values[0] = 1
    assert exp.reactors[1].experiment.actual_temperature.values[0] == 1
