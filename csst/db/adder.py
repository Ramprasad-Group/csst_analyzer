"""Functions for adding data to the database"""
from typing import Union, Optional, Dict
import logging

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
import numpy as np
from pinrex.db.models.csst import (
    CSSTExperiment,
    CSSTTemperatureProgram,
    CSSTReactor,
    CSSTProperty,
    CSSTExperimentPropertyValue,
    CSSTExperimentPropertyValues,
    CSSTReactorPropertyValues,
)

from csst.experiment import Experiment
from csst.experiment.models import (
    Reactor,
    PropertyValue,
    PropertyValues,
    TemperatureProgram,
)
from csst.db import getter

logger = logging.getLogger(__name__)


def add_experiment(experiment: Experiment, Session: Union[scoped_session, Session]):
    """Adds experiment data to experiment table

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    data = experiment.dict()
    logger.info(f"Searching for {data} in CSSTExperiment Table")
    with Session() as session:
        if session.query(CSSTExperiment).filter_by(**data).count() > 0:
            logger.info(f"{data} already added")
            return
        else:
            data["file_name"] = experiment.file_name
            logger.info(f"Adding CSST Experiment {data} to the database")
            exp = CSSTExperiment(**data)
            session.add(exp)
            session.commit()
            session.refresh(exp)
    add_experiment_property_value(exp.id, experiment.bottom_stir_rate, Session)
    add_experiment_property_values(exp.id, experiment.actual_temperature, Session)
    # use optional name since actual temperature will clash with set temperature
    add_experiment_property_values(
        exp.id, experiment.set_temperature, Session, "set_temperature"
    )
    add_experiment_property_values(
        exp.id, experiment.time_since_experiment_start, Session
    )
    add_experiment_property_values(exp.id, experiment.stir_rates, Session)


def add_experiment_property_values(
    experiment_id: int,
    prop: PropertyValues,
    Session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add experiment property values. Will add CSSTProperty if it is not present

    Args:
        experiment_id: CSSTExperiment id in database
        prop: Property values to add
        Session: session connected to the database
        prop_name: Optional name to use instead of prop.name. Default None
    """
    if not isinstance(prop, PropertyValues):
        msg = f"Only PropertyValues can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    add_property(prop_data, Session)
    with Session() as session:
        query = session.query(CSSTProperty).filter_by(**prop_data)
        getter.raise_lookup_error_if_query_count_is_not_one(query, "prop", prop_data)
        db_prop = query.first()
        data = {
            "csst_property_id": db_prop.id,
            "csst_experiment_id": experiment_id,
        }
        query = session.query(CSSTExperimentPropertyValues).filter_by(**data)
        if query.count() != 0:
            msg = f"PropertyValues for {data} already added"
            logger.warning(msg)
            raise LookupError(msg)
        values = prop.values
        if isinstance(values, np.ndarray):
            values = values.astype(np.float64)
        for i in range(len(values)):
            data["array_index"] = i
            data["value"] = values[i]
            session.add(CSSTExperimentPropertyValues(**data))
        session.commit()


def add_experiment_property_value(
    experiment_id: int,
    prop: PropertyValue,
    Session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add experiment property values. Will add CSSTProperty if it is not present

    Args:
        experiment_id: CSSTExperiment id in database
        prop: Property to add
        Session: session connected to the database
        prop_name: Optional name to use instead of prop.name
    """
    if not isinstance(prop, PropertyValue):
        msg = f"Only PropertyValue can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    add_property(prop_data, Session)
    with Session() as session:
        query = session.query(CSSTProperty).filter_by(**prop_data)
        getter.raise_lookup_error_if_query_count_is_not_one(query, "prop", prop_data)
        db_prop = query.first()
        data = {
            "csst_property_id": db_prop.id,
            "csst_experiment_id": experiment_id,
            "value": prop.value,
        }
        query = session.query(CSSTExperimentPropertyValue).filter_by(**data)
        if query.count() == 0:
            session.add(CSSTExperimentPropertyValue(**data))
            session.commit()
        else:
            msg = f"PropertyValue {data} already added"
            logger.warning(msg)
            raise LookupError(msg)


def add_temperature_program(
    temperature_program: TemperatureProgram, Session: Union[scoped_session, Session]
):
    """Adds temperature program to the temperature program table

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    data = temperature_program.dict()
    hash_ = temperature_program.hash()
    data["hash"] = hash_
    logger.info(f"Searching for {data} in CSSTTemperatureProgram table")
    with Session() as session:
        if (
            session.query(CSSTTemperatureProgram).filter(
                CSSTTemperatureProgram.hash == hash_
            )
        ).count() > 0:
            logger.info(f"{data} already added")
        else:
            logger.info(f"Adding CSST Temperature Program {data} to the database")
            session.add(CSSTTemperatureProgram(**data))
            session.commit()


def add_experiment_reactors(
    experiment: Experiment, Session: Union[scoped_session, Session]
):
    """Adds reactors from experiment to the reactor table. Experiment and
    temperature program must already be in the database.

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    # get temperature program and experiment ids
    experiment_id = getter.get_csst_experiment(experiment, Session).id
    temperature_program_id = getter.get_csst_temperature_program(
        experiment.temperature_program, Session
    ).id
    # add reactors
    logger.info(
        f"Adding reactors for experiment {experiment_id} and temperature"
        + f" program {temperature_program_id}"
    )
    for reactor in experiment.reactors:
        add_reactor(reactor, Session, experiment_id, temperature_program_id)


def add_reactor(
    reactor: Reactor,
    Session: Union[scoped_session, Session],
    experiment_id: int,
    temperature_program_id: int,
):
    """Add one reactor from experiment to the reactor table

    Args:
        reactor: reactor to add to the database
        Session: session connected to the database
        experiment_id: id from the database corresponding to the experiment the
            reactor is associated with
        temperature_program_id: id from the database corresponding to the temperature
            program the reactor is associated with
    """
    if not isinstance(reactor, Reactor):
        msg = f"Only Reactor can be added, not type {type(reactor)}"
        logger.warning(msg)
        raise ValueError(msg)
    # get lab polymer and solvent ids
    data = {
        "csst_experiment_id": experiment_id,
        "csst_temperature_program_id": temperature_program_id,
        "conc": reactor.conc.value,
        "conc_unit": reactor.conc.unit,
        "bret_pol_id": getter.get_lab_polymer_by_name(reactor.polymer, Session).id,
        "bret_sol_id": getter.get_lab_solvent_by_name(reactor.solvent, Session).id,
        "reactor_number": reactor.reactor_number
    }
    with Session() as session:
        if session.query(CSSTReactor).filter_by(**data).count() > 0:
            logger.info(f"Reactor {str(reactor)} already added")
            return
        db_reactor = CSSTReactor(**data)
        session.add(db_reactor)
        session.commit()
        session.refresh(db_reactor)
    add_reactor_property_values(db_reactor.id, reactor.transmission, Session)


def add_reactor_property_values(
    reactor_id: int,
    prop: PropertyValues,
    Session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add reactor property values. Will add CSSTProperty if it is not present

    Args:
        reactor_id: CSSTReactor id in database
        prop: Property values to add
        Session: session connected to the database
        prop_name: Optional name to use instead of prop.name. Default None
    """
    if not isinstance(prop, PropertyValues):
        msg = f"Only PropertyValues can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    add_property(prop_data, Session)
    with Session() as session:
        query = session.query(CSSTProperty).filter_by(**prop_data)
        getter.raise_lookup_error_if_query_count_is_not_one(query, "prop", prop_data)
        db_prop = query.first()
        data = {
            "csst_property_id": db_prop.id,
            "csst_reactor_id": reactor_id,
        }
        query = session.query(CSSTReactorPropertyValues).filter_by(**data)
        if query.count() != 0:
            msg = f"PropertyValues for {data} already added"
            logger.warning(msg)
            raise LookupError(msg)
        values = prop.values
        if isinstance(values, np.ndarray):
            values = values.astype(np.float64)
        for i in range(len(values)):
            data["array_index"] = i
            data["value"] = values[i]
            session.add(CSSTReactorPropertyValues(**data))
        session.commit()


def add_property(
    prop: Dict[str, str],
    Session: Union[scoped_session, Session],
):
    """Add property to CSSTProperty if it is not present"""
    with Session() as session:
        query = session.query(CSSTProperty).filter_by(**prop)
        if query.count() == 0:
            logger.info(f"Adding property {prop}")
            db_prop = session.add(CSSTProperty(**prop))
            session.commit()
        else:
            logger.info(f"Property {prop} already added")
