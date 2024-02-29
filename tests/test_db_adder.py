import pytest
import numpy as np

from csst.db.orm.csst import (
    CSSTExperiment,
    CSSTTemperatureProgram,
    CSSTProperty,
    CSSTReactorPropertyValues,
    CSSTExperimentPropertyValue,
    CSSTReactor,
    CSSTReactorProcessedTemperature,
)

from csst.experiment import Experiment
from csst.experiment.models import PropertyNameEnum, PropertyValue, PropertyValues
from csst.analyzer import Analyzer
from .fixtures.data import csste_1014, manual_1014, reactor  # noqa: F401


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


@pytest.mark.slow
def test_add_experiment(session, csste_1014):  # noqa: F811
    db.adder.add_experiment_and_or_get_id(
        csste_1014, session, upload_raw_properties=True
    )
    session.commit()
    assert (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment=csste_1014.start_of_experiment)
        .count()
    ) == 1
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
    db.adder.add_experiment_and_or_get_id(csste_1014, session)
    session.commit()
    assert (
        session.query(CSSTExperiment)
        .filter_by(start_of_experiment=csste_1014.start_of_experiment)
        .count()
    ) == 1

    # test single value properties
    prop = (
        session.query(CSSTProperty)
        .filter_by(
            name=csste_1014.bottom_stir_rate.name, unit=csste_1014.bottom_stir_rate.unit
        )
        .first()
    )
    val = (
        session.query(CSSTExperimentPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .first()
    )
    assert val.value == csste_1014.bottom_stir_rate.value
    assert prop.unit == csste_1014.bottom_stir_rate.unit

    # test multi value properties
    prop = (
        session.query(CSSTProperty)
        .filter_by(
            name=csste_1014.actual_temperature.name,
            unit=csste_1014.actual_temperature.unit,
        )
        .first()
    )
    assert prop.unit == csste_1014.actual_temperature.unit
    vals = (
        session.query(CSSTExperimentPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == csste_1014.actual_temperature.values[val.array_index]

    prop = (
        session.query(CSSTProperty)
        .filter_by(
            name=csste_1014.time_since_experiment_start.name,
            unit=csste_1014.time_since_experiment_start.unit,
        )
        .first()
    )
    assert prop.unit == csste_1014.time_since_experiment_start.unit
    vals = (
        session.query(CSSTExperimentPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert (
            val.value == csste_1014.time_since_experiment_start.values[val.array_index]
        )

    prop = (
        session.query(CSSTProperty)
        .filter_by(name=csste_1014.stir_rates.name, unit=csste_1014.stir_rates.unit)
        .first()
    )
    assert prop.unit == csste_1014.stir_rates.unit
    vals = (
        session.query(CSSTExperimentPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == csste_1014.stir_rates.values[val.array_index]

    prop = (
        session.query(CSSTProperty)
        .filter_by(name="set_temperature", unit=csste_1014.set_temperature.unit)
        .first()
    )
    assert prop.unit == csste_1014.set_temperature.unit
    vals = (
        session.query(CSSTExperimentPropertyValue)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == csste_1014.set_temperature.values[val.array_index]


def test_add_temperature_program_and_or_get_program_id(
    session, manual_1014
):  # noqa: F811
    db.adder.add_temperature_program_and_or_get_program_id(
        manual_1014.temperature_program, session
    )
    session.commit()
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
    db.adder.add_temperature_program_and_or_get_program_id(
        manual_1014.temperature_program, session
    )
    session.commit()
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


def test_add_reactor_property_values(session, manual_1014):  # noqa: F811
    reactor_id = 10000  # from database seed function in conftest
    prop = PropertyValue(name="bottom_stir_rate", unit="rpm", value=5)
    prop_data = {"name": prop.name, "unit": prop.unit}
    db.adder.add_property(prop_data, session)
    with pytest.raises(ValueError):
        db.adder.add_reactor_property_values(reactor_id, prop_data, session)
    prop = PropertyValues(name="temperature", unit="K", values=np.array([0, 1, 2, 3]))
    prop_data = {"name": prop.name, "unit": prop.unit}
    db.adder.add_property(prop_data, session)
    db.adder.add_reactor_property_values(reactor_id, prop, session)
    session.commit()
    prop_query = session.query(CSSTProperty).filter_by(
        name=PropertyNameEnum.TEMP, unit="K"
    )
    assert prop_query.count() == 1
    db_prop = prop_query.first()
    values = (
        session.query(CSSTReactorPropertyValues)
        .filter(
            CSSTReactorPropertyValues.csst_reactor_id == reactor_id,
            CSSTReactorPropertyValues.csst_property_id == db_prop.id,
        )
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


def test_add_experiment_property_value(session, manual_1014):  # noqa: F811
    experiment_id = 10000  # from database seed function in conftest
    prop = PropertyValues(name="temperature", unit="K", values=np.array([0, 1, 2, 3]))
    with pytest.raises(ValueError):
        db.adder.add_experiment_property_value(experiment_id, prop, session)
    prop = PropertyValue(name="bottom_stir_rate", unit="rpm", value=20)
    db.adder.add_property({"name": prop.name, "unit": prop.unit}, session)
    db.adder.add_experiment_property_value(experiment_id, prop, session)
    session.commit()
    prop_query = session.query(CSSTProperty).filter_by(name=prop.name, unit=prop.unit)
    assert prop_query.count() == 1
    db_prop = prop_query.first()
    query = session.query(CSSTExperimentPropertyValue).filter(
        CSSTExperimentPropertyValue.csst_experiment_id == experiment_id,
        CSSTExperimentPropertyValue.csst_property_id == db_prop.id,
    )
    assert query.count() == 1
    value = query.first()
    assert value.csst_experiment_id == experiment_id
    assert value.csst_property_id == db_prop.id
    assert value.value == 20
    with pytest.raises(LookupError, match=r"already added"):
        db.adder.add_experiment_property_value(experiment_id, prop, session)
    assert prop_query.count() == 1
    assert query.count() == 1


def test_add_reactor(session, reactor):  # noqa: F811
    db.adder.add_property(
        {"name": reactor.transmission.name, "unit": reactor.transmission.unit}, session
    )
    experiment_id = 10000
    temperature_program_id = 10000
    with pytest.raises(ValueError):
        db.adder.add_reactor({}, session, experiment_id, temperature_program_id)
    db.adder.add_reactor(reactor, session, experiment_id, temperature_program_id)
    session.commit()
    query = session.query(CSSTReactor).filter_by(
        conc=reactor.conc.value, conc_unit=reactor.conc.unit
    )
    assert query.count() == 1
    query.first()
    prop = (
        session.query(CSSTProperty)
        .filter_by(name=reactor.transmission.name, unit=reactor.transmission.unit)
        .first()
    )
    # test multivalue properties
    vals = (
        session.query(CSSTReactorPropertyValues)
        .filter_by(csst_property_id=prop.id)
        .all()
    )
    for val in vals:
        assert val.value == reactor.transmission.values[val.array_index]


@pytest.mark.slow
def test_add_experiment_reactors(session, csste_1014):  # noqa: F811
    """Needs both add_experiment and add_temperature_program_and_or_get_program_id test to pass"""
    # must add both experiment and temperature program first or lookup error will be raised
    old_num_props = session.query(CSSTProperty).count()
    exp_id = db.adder.add_experiment_and_or_get_id(csste_1014, session)
    temp_program_id = db.adder.add_temperature_program_and_or_get_program_id(
        csste_1014.temperature_program, session
    )
    db.adder.add_experiment_reactors(csste_1014, exp_id, temp_program_id, session)
    session.commit()
    # there should be 3 reactors added. Won't test if values added are correct as
    # that should have been accurately assessed by adding the single reactor test
    assert (
        session.query(CSSTReactor)
        .filter(CSSTReactor.csst_experiment_id < 10000)
        .count()
        == 3
    )
    assert session.query(CSSTProperty).count() == 7 + old_num_props


def test_add_processed_reactor(session):
    """Will fail if get experiments fails or analyzer fails"""
    old_db_count = session.query(CSSTReactorProcessedTemperature).count()
    exps = db.getter.get_experiments(Experiment(), session)
    exp = exps[0]
    analyzer = Analyzer()
    analyzer.add_experiment_reactors(exp)
    # test error is thrown if type isn't ProcessedReactor
    with pytest.raises(ValueError):
        db.adder.add_processed_reactor(analyzer, session)
    # should be added
    for reactor_ in analyzer.processed_reactors:
        db.adder.add_processed_reactor(session=session, reactor=reactor_)
        session.commit()
    # shouldn't be added
    for reactor_ in analyzer.processed_reactors:
        db.adder.add_processed_reactor(session=session, reactor=reactor_)
        session.commit()
    db_count = session.query(CSSTReactorProcessedTemperature).count() - old_db_count
    assert (
        len(analyzer.processed_reactors[0].temperatures)
        * len(analyzer.processed_reactors)
        == db_count
    )


def test_bad_add_processed_reactor(session):
    """Tests if reactor is added when experiment or reactor not added already"""
    old_db_count = session.query(CSSTReactorProcessedTemperature).count()
    exps = db.getter.get_experiments(Experiment(), session)
    exp = exps[0]
    exp.reactors = [exp.reactors[0]]
    old_lab_journal = exp.lab_journal
    exp.lab_journal = "changed to make query fail to find experiment"
    old_unit = exp.reactors[0].conc.unit
    exp.reactors[0].conc.unit = "changed to make query fail to find reactor"

    analyzer = Analyzer()
    analyzer.add_experiment_reactors(exp)
    # should fail becuase experiment can't be found
    for reactor_ in analyzer.processed_reactors:
        db.adder.add_processed_reactor(session=session, reactor=reactor_)
        session.commit()
    assert session.query(CSSTReactorProcessedTemperature).count() - old_db_count == 0

    exp.lab_journal = old_lab_journal
    # should fail becuase reactor can't be found
    for reactor_ in analyzer.processed_reactors:
        db.adder.add_processed_reactor(session=session, reactor=reactor_)
        session.commit()
    assert session.query(CSSTReactorProcessedTemperature).count() - old_db_count == 0

    exp.reactors[0].conc.unit = old_unit
    # should now pass since reactor and experiment query fixed
    for reactor_ in analyzer.processed_reactors:
        db.adder.add_processed_reactor(session=session, reactor=reactor_)
        session.commit()
    assert session.query(CSSTReactorProcessedTemperature).count() - old_db_count == len(
        analyzer.processed_reactors[0].temperatures
    )
