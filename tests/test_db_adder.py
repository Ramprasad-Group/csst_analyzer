import os

import pytest
import numpy as np

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
    CSSTExperiment,
    CSSTTemperatureProgram,
    CSSTProperty,
    CSSTReactorPropertyValues,
    CSSTReactorPropertyValue,
    CSSTReactor,
)

from csst.experiment.models import PropertyNameEnum, PropertyValue, PropertyValues
from .fixtures.data import csste_1014, manual_1014, reactor


def test_add_experiment(session, csste_1014):
    db.adder.add_experiment(csste_1014, session)
    experiment = (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment=csste_1014.start_of_experiment)
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
    db.adder.add_experiment(csste_1014, session)
    assert (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment=csste_1014.start_of_experiment)
        .count()
    ) == 1


def test_add_temperature_program(session, manual_1014):
    db.adder.add_temperature_program(manual_1014.temperature_program, session)
    temp_program = (
        session.query(CSSTTemperatureProgram)
        .filter(CSSTTemperatureProgram.hash == manual_1014.temperature_program.hash())
        .first()
    )
    assert temp_program.block == manual_1014.temperature_program.block
    assert temp_program.solvent_tune == [
        step.dict() for step in manual_1014.temperature_program.solvent_tune
    ]
    assert temp_program.sample_load == [
        step.dict() for step in manual_1014.temperature_program.sample_load
    ]
    assert temp_program.experiment == [
        step.dict() for step in manual_1014.temperature_program.experiment
    ]
    db.adder.add_temperature_program(manual_1014.temperature_program, session)
    assert (
        session.query(CSSTTemperatureProgram)
        .filter(CSSTTemperatureProgram.hash == manual_1014.temperature_program.hash())
        .count()
    ) == 1


def test_add_property(session):
    prop = {"name": PropertyNameEnum.TEMP, "unit": "K"}
    db.adder.add_property(prop, session)
    db_prop = session.query(CSSTProperty).filter_by(**prop).first()
    assert db_prop.name == prop["name"]
    assert db_prop.unit == prop["unit"]
    db.adder.add_property(prop, session)
    assert session.query(CSSTProperty).filter_by(**prop).count() == 1


def test_add_reactor_propery_values(session, manual_1014):
    reactor_id = 10000  # from database seed function in conftest
    prop = PropertyValue(name="bottom_stir_rate", unit="rpm", value=5)
    with pytest.raises(ValueError):
        db.adder.add_reactor_property_values(reactor_id, prop, session)
    prop = PropertyValues(name="temperature", unit="K", values=np.array([0, 1, 2, 3]))
    db.adder.add_reactor_property_values(reactor_id, prop, session)
    prop_query = session.query(CSSTProperty).filter_by(
        name=PropertyNameEnum.TEMP, unit="K"
    )
    assert prop_query.count() == 1
    db_prop = prop_query.first()
    values = (
        session.query(CSSTReactorPropertyValues)
        .filter(CSSTReactorPropertyValues.csst_reactor_id == reactor_id)
        .all()
    )
    for value in values:
        assert value.csst_reactor_id == reactor_id
        assert value.csst_property_id == db_prop.id
        assert value.array_index == value.value
    assert len(values) == 4
    with pytest.raises(LookupError, match=r"already added"):
        db.adder.add_reactor_property_values(reactor_id, prop, session)
    assert prop_query.count() == 1


def test_add_reactor_propery_value(session, manual_1014):
    reactor_id = 10000  # from database seed function in conftest
    prop = PropertyValues(name="temperature", unit="K", values=np.array([0, 1, 2, 3]))
    with pytest.raises(ValueError):
        db.adder.add_reactor_property_value(reactor_id, prop, session)
    prop = PropertyValue(name="bottom_stir_rate", unit="rpm", value=20)
    db.adder.add_reactor_property_value(reactor_id, prop, session)
    prop_query = session.query(CSSTProperty).filter_by(name=prop.name, unit=prop.unit)
    assert prop_query.count() == 1
    db_prop = prop_query.first()
    query = session.query(CSSTReactorPropertyValue).filter(
        CSSTReactorPropertyValue.csst_reactor_id == reactor_id
    )
    assert query.count() == 1
    value = query.first()
    assert value.csst_reactor_id == reactor_id
    assert value.csst_property_id == db_prop.id
    assert value.value == 20
    with pytest.raises(LookupError, match=r"already added"):
        db.adder.add_reactor_property_value(reactor_id, prop, session)
    assert prop_query.count() == 1
    assert query.count() == 1
    # test that an error isn't thrown if we change the prop name
    db.adder.add_reactor_property_value(reactor_id, prop, session, prop_name="test")
    prop_query = session.query(CSSTProperty).filter_by(name="test", unit=prop.unit)
    assert prop_query.count() == 1
    query = session.query(CSSTReactorPropertyValue).filter(
        CSSTReactorPropertyValue.csst_reactor_id == reactor_id
    )
    assert query.count() == 2


def test_add_reactor(session, reactor):
    experiment_id = 10000
    temperature_program_id = 10000
    with pytest.raises(ValueError):
        db.adder.add_reactor({}, session, experiment_id, temperature_program_id)
    db.adder.add_reactor(reactor, session, experiment_id, temperature_program_id)
    # should have 6 properties added
    assert session.query(CSSTProperty).count() == 6
    query = session.query(CSSTReactor).filter_by(
        conc=reactor.conc.value, conc_unit=reactor.conc.unit
    )
    assert query.count() == 1
    db_reactor = query.first()
    # test single value properties
    prop = (
        session.query(CSSTProperty)
        .filter_by(name=reactor.bottom_stir_rate.name)
        .first()
    )
    val = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .first()
    )
    assert val.value == reactor.bottom_stir_rate.value
    assert prop.unit == reactor.bottom_stir_rate.unit

    # test multivalue properties
    prop = session.query(CSSTProperty).filter_by(name=reactor.transmission.name).first()
    assert prop.unit == reactor.transmission.unit
    vals = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.transmission.values[val.array_index]

    prop = (
        session.query(CSSTProperty)
        .filter_by(name=reactor.actual_temperature.name)
        .first()
    )
    assert prop.unit == reactor.actual_temperature.unit
    vals = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.actual_temperature.values[val.array_index]

    prop = (
        session.query(CSSTProperty)
        .filter_by(name=reactor.time_since_experiment_start.name)
        .first()
    )
    assert prop.unit == reactor.time_since_experiment_start.unit
    vals = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.time_since_experiment_start.values[val.array_index]

    prop = session.query(CSSTProperty).filter_by(name=reactor.stir_rates.name).first()
    assert prop.unit == reactor.stir_rates.unit
    vals = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.stir_rates.values[val.array_index]

    prop = session.query(CSSTProperty).filter_by(name="set_temperature").first()
    assert prop.unit == reactor.set_temperature.unit
    vals = (
        session.query(CSSTReactorPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.set_temperature.values[val.array_index]


@pytest.mark.slow
def test_add_experiment_reactors(session, csste_1014):
    """Needs both add_experiment and add_temperature_program test to pass"""
    # must add both experiment and temperature program first or lookup error will be raised
    with pytest.raises(LookupError):
        db.adder.add_experiment_reactors(csste_1014, session)
    db.adder.add_experiment(csste_1014, session)
    with pytest.raises(LookupError):
        db.adder.add_experiment_reactors(csste_1014, session)
    db.adder.add_temperature_program(csste_1014.temperature_program, session)
    db.adder.add_experiment_reactors(csste_1014, session)
    # there should be 3 reactors added. Won't test if values added are correct as
    # that should have been accurately assessed by adding the single reactor test
    assert (
        session.query(CSSTReactor)
        .filter(CSSTReactor.csst_experiment_id != 10000)
        .count()
        == 3
    )
    assert session.query(CSSTProperty).count() == 6
