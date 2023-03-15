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

from pinrex.db.models.csst import CSSTExperiment, CSSTTemperatureProgram

from .fixtures.data import csste_1014, manual_1014


def test_raise_lookup_error_if_query_count_is_not_one(session, manual_1014):
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


def test_get_experiment(session, manual_1014):
    """Will likely fail if raise_lookup_error_if_query_count_is_not_one fails"""
    session.add(CSSTExperiment(**manual_1014.dict()))
    session.commit()
    exp = db.getter.get_experiment(manual_1014, session)
    assert exp.version == manual_1014.version
    assert exp.start_of_experiment == manual_1014.start_of_experiment


def test_get_temperature_program(session, manual_1014):
    """Will likely fail if raise_lookup_error_if_query_count_is_not_one fails"""
    data = manual_1014.temperature_program.dict()
    data["hash"] = manual_1014.temperature_program.hash()
    session.add(CSSTTemperatureProgram(**data))
    session.commit()
    program = db.getter.get_temperature_program(
        manual_1014.temperature_program, session
    )
    assert program.block == manual_1014.temperature_program.block
    assert program.solvent_tune == [
        item.dict() for item in manual_1014.temperature_program.solvent_tune
    ]


def test_get_lab_polymer_by_name(session):
    """Will likely fail if raise_lookup_error_if_list_count_is_not_one fails"""
    pol = db.getter.get_lab_polymer_by_name("PEO", session)
    assert pol.supplier == "thermofischer"
    assert pol.name == "PEG"


def test_get_lab_solvent_by_name(session):
    """Will likely fail if raise_lookup_error_if_list_count_is_not_one fails"""
    sol = db.getter.get_lab_solvent_by_name("MeOH", session)
    assert sol.name == "methanol"
    assert sol.percent_purity == 99
