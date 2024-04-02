"""Functions for adding data to the database"""
from typing import Union, Optional, Dict
import logging

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
import numpy as np
from csst.db.orm.csst import (
    CSSTExperiment,
    CSSTTemperatureProgram,
    CSSTReactor,
    CSSTProperty,
    CSSTExperimentPropertyValue,
    CSSTExperimentPropertyValues,
    CSSTReactorPropertyValues,
    CSSTReactorProcessedTemperature,
)

from csst.experiment import Experiment
from csst.experiment.models import (
    Reactor,
    PropertyValue,
    PropertyValues,
    TemperatureProgram,
)
from csst.processor.models import ProcessedReactor
from csst.db import getter

logger = logging.getLogger(__name__)


def add_experiment(
    experiment: Experiment,
    session: Union[scoped_session, Session],
    upload_raw_properties: bool = False,
):
    """Adds experiment data, temperature_program, and reactor data to database

    Args:
        experiment: experiment to add to table
        session: instantiated session connected to the database
    """
    exp_id = add_experiment_and_or_get_id(
        experiment=experiment,
        session=session,
        upload_raw_properties=upload_raw_properties,
    )
    temp_program_id = add_temperature_program_and_or_get_program_id(
        temperature_program=experiment.temperature_program, session=session
    )
    add_experiment_reactors(
        experiment=experiment,
        experiment_id=exp_id,
        temperature_program_id=temp_program_id,
        session=session,
        upload_raw_properties=upload_raw_properties,
    )


def add_experiment_and_or_get_id(
    experiment: Experiment,
    session: Union[scoped_session, Session],
    upload_raw_properties: bool = False,
) -> int:
    """Adds experiment data to experiment table

    Args:
        experiment: experiment to add to table
        session: instantiated session connected to the database
    """
    data = experiment.dict()
    search_data = {
        key: value
        for key, value in data.items()
        if key not in ["description", "lab_journal"]
    }
    logger.info(f"Searching for {data} in CSSTExperiment Table")
    query = session.query(CSSTExperiment).filter_by(**search_data)
    if query.count() > 0:
        logger.info(f"{data} already added")
        return query.first().id
    else:
        # we want to add all properties first as we don't care about this being an
        # atomic input
        for index, prop in enumerate(
            [
                experiment.bottom_stir_rate,
                experiment.actual_temperature,
                experiment.set_temperature,
                experiment.time_since_experiment_start,
                experiment.stir_rates,
                experiment.top_stir_rate,
            ]
        ):
            if prop is None:
                continue
            prop_data = {"name": prop.name, "unit": prop.unit}
            if index == 2:
                prop_data["name"] = "set_temperature"
            add_property(prop_data, session)
        for reactor in experiment.reactors:
            prop_data = {
                "name": reactor.transmission.name,
                "unit": reactor.transmission.unit,
            }
            add_property(prop_data, session)

        data["file_name"] = experiment.file_name
        logger.info(f"Adding CSST Experiment {data} to the database")
        exp = CSSTExperiment(**data)
        session.add(exp)
        session.flush()
        session.refresh(exp)
    if experiment.bottom_stir_rate is not None:
        add_experiment_property_value(exp.id, experiment.bottom_stir_rate, session)
    if experiment.top_stir_rate is not None:
        add_experiment_property_value(exp.id, experiment.top_stir_rate, session)
    if upload_raw_properties:
        add_experiment_property_values(exp.id, experiment.actual_temperature, session)
        # use optional name since actual temperature will clash with set temperature
        add_experiment_property_values(
            exp.id, experiment.set_temperature, session, "set_temperature"
        )
        add_experiment_property_values(
            exp.id, experiment.time_since_experiment_start, session
        )
        add_experiment_property_values(exp.id, experiment.stir_rates, session)
    return exp.id


def add_experiment_property_values(
    experiment_id: int,
    prop: PropertyValues,
    session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add experiment property values. Will add CSSTProperty if it is not present

    Args:
        experiment_id: CSSTExperiment id in database
        prop: Property values to add
        session: instantiated session connected to the database
        prop_name: Optional name to use instead of prop.name. Default None
    """
    if not isinstance(prop, PropertyValues):
        msg = f"Only PropertyValues can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    prop_id = getter.get_property_id(prop_data, session)
    data = {
        "csst_property_id": prop_id,
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


def add_experiment_property_value(
    experiment_id: int,
    prop: PropertyValue,
    session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add experiment property values. Will add CSSTProperty if it is not present

    Args:
        experiment_id: CSSTExperiment id in database
        prop: Property to add
        session: instantiated session connected to the database
        prop_name: Optional name to use instead of prop.name
    """
    if not isinstance(prop, PropertyValue):
        msg = f"Only PropertyValue can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    prop_id = getter.get_property_id(prop_data, session)
    data = {
        "csst_property_id": prop_id,
        "csst_experiment_id": experiment_id,
        "value": prop.value,
    }
    query = session.query(CSSTExperimentPropertyValue).filter_by(**data)
    if query.count() == 0:
        session.add(CSSTExperimentPropertyValue(**data))
    else:
        msg = f"PropertyValue {data} already added"
        logger.warning(msg)
        raise LookupError(msg)


def add_temperature_program_and_or_get_program_id(
    temperature_program: TemperatureProgram, session: Union[scoped_session, Session]
) -> int:
    """Adds temperature program to the temperature program table if it doens't exist
    and gets the program id

    Args:
        experiment: experiment to add to table
        session: instantiated session connected to the database
    """
    data = temperature_program.dict()
    hash_ = temperature_program.hash()
    data["hash"] = hash_
    logger.info(f"Searching for {data} in CSSTTemperatureProgram table")
    query = session.query(CSSTTemperatureProgram).filter(
        CSSTTemperatureProgram.hash == hash_
    )
    if query.count() > 0:
        logger.info(f"{data} already added")
        return query.first().id
    else:
        logger.info(f"Adding CSST Temperature Program {data} to the database")
        program = CSSTTemperatureProgram(**data)
        session.add(program)
        session.flush()
        session.refresh(program)
        return program.id


def add_experiment_reactors(
    experiment: Experiment,
    experiment_id: int,
    temperature_program_id: int,
    session: Union[scoped_session, Session],
    upload_raw_properties: bool = False,
):
    """Adds reactors from experiment to the reactor table.

    Args:
        experiment_id: id linking to appropraite experiment
        temperature_program_id: id linking to appropraite temperature program
        session: instantiated session connected to the database
    """
    # add reactors
    logger.info(
        f"Adding reactors for experiment {experiment_id} and temperature"
        + f" program {temperature_program_id}"
    )
    for reactor in experiment.reactors:
        add_reactor(
            reactor,
            session,
            experiment_id,
            temperature_program_id,
            upload_raw_properties,
        )


def add_reactor(
    reactor: Reactor,
    session: Union[scoped_session, Session],
    experiment_id: int,
    temperature_program_id: int,
    upload_raw_properties: bool = False,
):
    """Add one reactor from experiment to the reactor table

    Args:
        reactor: reactor to add to the database
        session: instantiated session connected to the database
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
    lab_pol_id = reactor.polymer_id
    if lab_pol_id is None:
        lab_pol_id = getter.get_lab_polymer_by_name(reactor.polymer, session).id
    lab_sol_id = reactor.solvent_id
    if lab_sol_id is None:
        lab_sol_id = getter.get_lab_solvent_by_name(reactor.solvent, session).id
    data = {
        "csst_experiment_id": experiment_id,
        "csst_temperature_program_id": temperature_program_id,
        "conc": reactor.conc.value,
        "conc_unit": reactor.conc.unit,
        "lab_pol_id": lab_pol_id,
        "lab_sol_id": lab_sol_id,
        "reactor_number": reactor.reactor_number,
    }
    if session.query(CSSTReactor).filter_by(**data).count() > 0:
        logger.info(f"Reactor {str(reactor)} already added")
        return
    db_reactor = CSSTReactor(**data)
    session.add(db_reactor)
    session.flush()
    session.refresh(db_reactor)
    if upload_raw_properties:
        add_reactor_property_values(db_reactor.id, reactor.transmission, session)


def add_reactor_property_values(
    reactor_id: int,
    prop: PropertyValues,
    session: Union[scoped_session, Session],
    prop_name: Optional[str] = None,
):
    """Add reactor property values. Will add CSSTProperty if it is not present

    Args:
        reactor_id: CSSTReactor id in database
        prop: Property values to add
        session: instantiated session connected to the database
        prop_name: Optional name to use instead of prop.name. Default None
    """
    if not isinstance(prop, PropertyValues):
        msg = f"Only PropertyValues can be added, not type {type(prop)}"
        logger.warning(msg)
        raise ValueError(msg)
    prop_data = {"name": prop.name, "unit": prop.unit}
    if prop_name is not None:
        prop_data["name"] = prop_name
    prop_id = getter.get_property_id(prop_data, session)
    data = {
        "csst_property_id": prop_id,
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


def add_property(
    prop: Dict[str, str],
    session: Union[scoped_session, Session],
) -> int:
    """Add property to CSSTProperty if it is not present and gets the property
    id
    """
    query = session.query(CSSTProperty).filter_by(**prop)
    if query.count() == 0:
        logger.info(f"Adding property {prop}")
        prop = CSSTProperty(**prop)
        session.add(prop)
        session.flush()
    else:
        logger.info(f"Property {prop} already added")


def add_processed_reactor(
    reactor: ProcessedReactor,
    session: Union[scoped_session, Session],
):
    if not isinstance(reactor, ProcessedReactor):
        msg = f"Only ProcessedReactor can be added, not type {type(reactor)}"
        logger.warning(msg)
        raise ValueError(msg)
    search_data = {
        key: value
        for key, value in reactor.unprocessed_reactor.experiment.dict().items()
        if key not in ["description", "lab_journal"]
    }
    exp = session.query(CSSTExperiment).filter_by(**search_data).first()
    if exp is None:
        logger.warning(search_data)
        msg = (
            "The unprocessed reactor experiment has not been added to the database yet."
        )
        logger.warning(msg)
        return
    lab_pol_id = reactor.unprocessed_reactor.polymer_id
    lab_sol_id = reactor.unprocessed_reactor.solvent_id
    if lab_pol_id is None:
        lab_pol_id = getter.get_lab_polymer_by_name(
            reactor.unprocessed_reactor.polymer, session
        ).id
    if lab_sol_id is None:
        lab_sol_id = getter.get_lab_solvent_by_name(
            reactor.unprocessed_reactor.solvent, session
        ).id
    data = {
        "csst_experiment_id": exp.id,
        "conc": reactor.unprocessed_reactor.conc.value,
        "conc_unit": reactor.unprocessed_reactor.conc.unit,
        "lab_pol_id": lab_pol_id,
        "lab_sol_id": lab_sol_id,
        "reactor_number": reactor.unprocessed_reactor.reactor_number,
    }
    unprocessed_reactor = session.query(CSSTReactor).filter_by(**data).first()
    if unprocessed_reactor is None:
        logger.info(f"{data}")
        logger.info("The unprocessed reactor has not been added to the database yet.")
        return
    if (
        session.query(CSSTReactorProcessedTemperature)
        .filter_by(csst_reactor_id=unprocessed_reactor.id)
        .count()
        > 0
    ):
        logger.info("Processed data has already been added for this reactor.")
        return
    for temp in reactor.temperatures:
        data = temp.dict()
        data["csst_reactor_id"] = unprocessed_reactor.id
        session.add(CSSTReactorProcessedTemperature(**data))
    session.flush()
