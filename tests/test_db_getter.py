import pytest
import numpy as np

from pinrex.db.models.csst import CSSTExperiment, CSSTTemperatureProgram

from csst.experiment import Experiment
from csst.experiment.models import PropertyNameEnum, TemperatureSettingEnum
from .fixtures.data import csste_1014, manual_1014  # noqa: F401

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


def test_raise_lookup_error_if_query_count_is_not_one(
    session, manual_1014
):  # noqa: F811
    with session() as sess:
        query = sess.query(CSSTExperiment).filter_by(**manual_1014.dict())
        with pytest.raises(LookupError, match=r"No experiment associated with"):
            db.getter.raise_lookup_error_if_query_count_is_not_one(
                query, "experiment", manual_1014.dict()
            )
        sess.add(CSSTExperiment(**manual_1014.dict()))
        sess.commit()
        # no error should be raised
        db.getter.raise_lookup_error_if_query_count_is_not_one(
            query, "experiment", manual_1014.dict()
        )
        sess.add(CSSTExperiment(**manual_1014.dict()))
        sess.commit()
        with pytest.raises(LookupError, match=r"Multiple experiments associated with"):
            db.getter.raise_lookup_error_if_query_count_is_not_one(
                query, "experiment", manual_1014.dict()
            )


def test_raise_lookup_error_if_list_count_is_not_one():
    with pytest.raises(LookupError, match=r"No test associated with"):
        db.getter.raise_lookup_error_if_list_count_is_not_one([], "test", "test")
    with pytest.raises(LookupError, match=r"Multiple tests associated with"):
        db.getter.raise_lookup_error_if_list_count_is_not_one([1, 2], "test", "test")


def test_get_csst_experiment(session, manual_1014):  # noqa: F811
    """Will likely fail if raise_lookup_error_if_query_count_is_not_one fails"""
    session.add(CSSTExperiment(**manual_1014.dict()))
    session.commit()
    exp = db.getter.get_csst_experiment(manual_1014, session)
    assert exp.version == manual_1014.version
    assert exp.start_of_experiment == manual_1014.start_of_experiment


def test_get_csst_temperature_program(session, manual_1014):  # noqa: F811
    """Will likely fail if raise_lookup_error_if_query_count_is_not_one fails"""
    data = manual_1014.temperature_program.dict()
    data["hash"] = manual_1014.temperature_program.hash()
    session.add(CSSTTemperatureProgram(**data))
    session.commit()
    program = db.getter.get_csst_temperature_program(
        manual_1014.temperature_program, session
    )
    assert program.block == manual_1014.temperature_program.block
    assert program.solvent_tune == [
        item.dict() for item in manual_1014.temperature_program.solvent_tune
    ]


def test_get_lab_polymer_by_name(session):
    """Will likely fail if raise_lookup_error_if_list_count_is_not_one fails"""
    pol = db.getter.get_lab_polymer_by_name("PEO", session)
    assert pol.supplier == "Alfa Aesar"
    assert pol.name == "PEO"


def test_get_lab_solvent_by_name(session):
    """Will likely fail if raise_lookup_error_if_list_count_is_not_one fails"""
    sol = db.getter.get_lab_solvent_by_name("MethANol", session)
    assert sol.name == "methanol"
    assert sol.percent_purity == 99


def test_get_csst_experiments(session):
    exp = Experiment()
    exps = db.getter.get_csst_experiments(exp, session)
    assert len(exps) == 2
    exp.version = "test"
    exp.experiment_details = "test"
    exp.experiment_number = "test"
    exp.experimenter = "test"
    exp.project = "test"
    exps = db.getter.get_csst_experiments(exp, session)
    assert len(exps) == 1
    exp.experimenter = "Joe"
    exps = db.getter.get_csst_experiments(exp, session)
    assert len(exps) == 0
    exp.experiment_details = None
    exp.experiment_number = None
    exps = db.getter.get_csst_experiments(exp, session)
    exp.experimenter = None
    exps = db.getter.get_csst_experiments(exp, session)
    assert len(exps) == 2


def test_get_csst_reactors_by_experiment_id(session):
    reactors = db.getter.get_csst_reactors_by_experiment_id(10000, session)
    assert len(reactors) == 3
    reactors = db.getter.get_csst_reactors_by_experiment_id(10001, session)
    assert len(reactors) == 1
    reactors = db.getter.get_csst_reactors_by_experiment_id(1, session)
    assert len(reactors) == 0


def test_get_experiment_property_value_by_experiment_id(session):
    for i in range(10000, 10002):
        props = db.getter.get_experiment_property_value_by_experiment_id(i, session)
        assert len(props) == 1
        prop = props[PropertyNameEnum.BOTTOM_STIR_RATE]
        assert prop.value == i
        assert prop.unit == "test"
        assert prop.name == PropertyNameEnum.BOTTOM_STIR_RATE


def test_get_experiment_property_values_by_experiment_id(session):
    for i in range(10000, 10002):
        props = db.getter.get_experiment_property_values_by_experiment_id(i, session)
        assert len(props) == 4
        for prop in [
            PropertyNameEnum.TEMP,
            PropertyNameEnum.STIR_RATE,
            PropertyNameEnum.TIME,
            "set_temperature",
        ]:
            prop_values = props[prop]
            assert np.array_equal(prop_values.values, list(range(i * 10, i * 10 + 10)))
            assert prop_values.unit == "test"
            if prop != "set_temperature":
                assert prop_values.name == prop
            else:
                assert prop_values.name == PropertyNameEnum.TEMP


def test_get_reactor_property_values_by_experiment_id(session):
    for i in range(10000, 10004):
        props = db.getter.get_reactor_property_values_by_reactor_id(i, session)
        assert len(props) == 1
        for prop in [PropertyNameEnum.TRANS]:
            prop_values = props[prop]
            assert np.array_equal(prop_values.values, list(range(i * 10, i * 10 + 10)))
            assert prop_values.unit == "test"
            assert prop_values.name == prop


def test_get_temperature_program_by_id(session):
    temperature_program = db.getter.get_temperature_program_by_id(10000, session)
    assert temperature_program.solvent_tune[0].setting == TemperatureSettingEnum.HEAT
    assert temperature_program.solvent_tune[0].to.value == 20
    assert temperature_program.solvent_tune[0].rate.name == "temperature_change_rate"


def test_get_experiments(session):
    exps = db.getter.get_experiments(Experiment(), session)
    assert len(exps) == 2
