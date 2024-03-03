"""Functions for getting data from the database"""
from datetime import datetime
from typing import Union, List, Dict, Optional
import logging

import numpy as np
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from csst.db.orm.polymer import LabPolymer
from csst.db.orm.solvent import LabSolvent
from csst.db.orm.csst import (
    CSSTTemperatureProgram,
    CSSTExperiment,
    CSSTReactor,
    CSSTExperimentPropertyValue,
    CSSTExperimentPropertyValues,
    CSSTReactorPropertyValues,
    CSSTProperty,
)

from csst.experiment import Experiment
from csst.experiment.models import (
    TemperatureProgram,
    PropertyNameEnum,
    Reactor,
    PropertyValue,
    PropertyValues,
)
from csst.experiment.helpers import remove_keys_with_null_values_in_dict

logger = logging.getLogger(__name__)


def load_from_db(
    session: Union[Session, scoped_session],
    file_name: Optional[str] = None,
    version: Optional[str] = None,
    experiment_details: Optional[str] = None,
    experiment_number: Optional[str] = None,
    experimenter: Optional[str] = None,
    project: Optional[str] = None,
    lab_journal: Optional[str] = None,
    description: Optional[List[str]] = None,
    start_of_experiment: Optional[datetime] = None,
) -> List[Experiment]:
    """Pass any relavent experiment details to return a list of experiments
    that contain them.

    Args:
        session: instantiated connected to the database.
        file_name (str): name of the original data file
        version (str): version of the data file
        experiment_details (str):
        experiment_number (str):
        experimenter (str):
        project (str):
        lab_journal (str):
        description (List[str]): Description information with each new line of the
            description appended to a list
        start_of_experiment (datetime):
            date the experiment started

    Returns:
        List of experiments returned that match all of the
        passed experiment details. If no details passed, all experiments are
        returned.

    """
    obj = Experiment()
    obj.file_name = file_name
    obj.version = version
    obj.experiment_details = experiment_details
    obj.experiment_number = experiment_number
    obj.experimenter = experimenter
    obj.project = project
    obj.lab_journal = lab_journal
    obj.description = description
    obj.start_of_experiment = start_of_experiment
    return get_experiments_from_experiment_details(obj, session)


def get_experiments_from_experiment_details(
    experiment: Experiment, session: Union[scoped_session, Session]
) -> List[Experiment]:
    """Gets a list of experiments that match the experiment metadata passed

    Args:
        experiment: experiment object that has any experiment details
        (values returned by experiment.dict()) filled out
        session: instantiated session connected to the database
    """
    return get_experiments(experiment, session)


def get_experiments(
    experiment: Experiment, session: Union[scoped_session, Session]
) -> List[Experiment]:
    """Gets all experiments associated with the experiment dict data"""
    experiments = []
    exps = get_csst_experiments(experiment, session)
    if len(exps) == 0:
        return experiments
    for exp in exps:
        reactors = get_csst_reactors_by_experiment_id(exp.id, session)
        temp_program = get_temperature_program_by_id(
            reactors[0].csst_temperature_program_id, session
        )
        exp_value_properties = get_experiment_property_value_by_experiment_id(
            exp.id, session
        )
        exp_values_properties = get_experiment_property_values_by_experiment_id(
            exp.id, session
        )
        reactors = [
            (reactor, get_reactor_property_values_by_reactor_id(reactor.id, session))
            for reactor in reactors
        ]
        experiment = Experiment()
        experiment.file_name = exp.file_name
        experiment.version = exp.version
        experiment.experiment_details = exp.experiment_details
        experiment.experiment_number = exp.experiment_number
        experiment.experimenter = exp.experimenter
        experiment.project = exp.project
        experiment.lab_journal = exp.lab_journal
        experiment.description = exp.description.split("\n")
        experiment.start_of_experiment = exp.start_of_experiment

        # data details
        experiment.temperature_program = temp_program
        experiment.bottom_stir_rate = None
        experiment.top_stir_rate = None
        if PropertyNameEnum.BOTTOM_STIR_RATE in exp_value_properties:
            experiment.bottom_stir_rate = exp_value_properties[
                PropertyNameEnum.BOTTOM_STIR_RATE
            ]
        if PropertyNameEnum.TOP_STIR_RATE in exp_value_properties:
            experiment.top_stir_rate = exp_value_properties[
                PropertyNameEnum.TOP_STIR_RATE
            ]

        experiment.set_temperature = exp_values_properties["set_temperature"]
        experiment.actual_temperature = exp_values_properties[PropertyNameEnum.TEMP]
        experiment.time_since_experiment_start = exp_values_properties[
            PropertyNameEnum.TIME
        ]
        dt = experiment.get_timestep_of_experiment()
        experiment.ramp_state = experiment.create_ramp_state(
            experiment.actual_temperature.values, dt
        )
        experiment.stir_rates = exp_values_properties[PropertyNameEnum.STIR_RATE]
        exp_reactors = [
            Reactor(
                solvent=get_lab_solvent_by_id(reactor.lab_sol_id, session).name,
                polymer=get_lab_polymer_by_id(reactor.lab_pol_id, session).name,
                polymer_id=reactor.lab_pol_id,
                solvent_id=reactor.lab_sol_id,
                reactor_number=reactor.reactor_number,
                conc=PropertyValue(
                    name=PropertyNameEnum.CONC,
                    unit=reactor.conc_unit,
                    value=reactor.conc,
                ),
                transmission=reactor_prop[PropertyNameEnum.TRANS],
                filtered_transmission=experiment.filter_transmission(
                    reactor_prop[PropertyNameEnum.TRANS].values, dt
                ),
                experiment=experiment,
            )
            for reactor, reactor_prop in reactors
        ]
        experiment.reactors = exp_reactors
        experiments.append(experiment)
    return experiments


def get_csst_experiments(
    experiment: Experiment, session: Union[scoped_session, Session]
) -> List[CSSTExperiment]:
    return (
        session.query(CSSTExperiment)
        .filter_by(**remove_keys_with_null_values_in_dict(experiment.dict()))
        .all()
    )


def get_csst_reactors_by_experiment_id(
    experiment_id: int, session: Union[scoped_session, Session]
) -> List[CSSTReactor]:
    return session.query(CSSTReactor).filter_by(csst_experiment_id=experiment_id).all()


def get_temperature_program_by_id(
    id_: int, session: Union[scoped_session, Session]
) -> TemperatureProgram:
    temp_program = session.query(CSSTTemperatureProgram).filter_by(id=id_).first()
    return TemperatureProgram(
        block=temp_program.block,
        solvent_tune=temp_program.solvent_tune,
        sample_load=temp_program.sample_load,
        experiment=temp_program.experiment,
    )


def get_lab_polymer_by_id(
    id_: int, session: Union[scoped_session, Session]
) -> LabPolymer:
    return session.query(LabPolymer).filter_by(id=id_).first()


def get_lab_solvent_by_id(
    id_: int, session: Union[scoped_session, Session]
) -> LabSolvent:
    return session.query(LabSolvent).filter_by(id=id_).first()


def get_experiment_property_value_by_experiment_id(
    experiment_id: int, session: Union[scoped_session, Session]
) -> Dict[str, PropertyValue]:
    properties = {}
    for prop_id in (
        session.query(CSSTExperimentPropertyValue.csst_property_id)
        .filter_by(csst_experiment_id=experiment_id)
        .distinct()
    ):
        prop = session.query(CSSTProperty).filter_by(id=prop_id[0]).first()
        value = (
            session.query(CSSTExperimentPropertyValue)
            .filter_by(csst_experiment_id=experiment_id, csst_property_id=prop.id)
            .first()
        )
        properties[prop.name] = PropertyValue(
            name=prop.name, unit=prop.unit, value=value.value
        )
    return properties


def get_experiment_property_values_by_experiment_id(
    experiment_id: int, session: Union[scoped_session, Session]
) -> Dict[str, PropertyValues]:
    properties = {}
    for prop_id in (
        session.query(CSSTExperimentPropertyValues.csst_property_id)
        .filter_by(csst_experiment_id=experiment_id)
        .distinct()
    ):
        prop = session.query(CSSTProperty).filter_by(id=prop_id[0]).first()
        values = (
            session.query(CSSTExperimentPropertyValues)
            .filter_by(csst_experiment_id=experiment_id, csst_property_id=prop.id)
            .all()
        )
        values = {value.array_index: value.value for value in values}
        arr = []
        for i in range(len(values)):
            arr.append(values[i])
        if prop.name != "set_temperature":
            properties[prop.name] = PropertyValues(
                name=prop.name, unit=prop.unit, values=np.array(arr)
            )
        else:
            properties[prop.name] = PropertyValues(
                name="temperature", unit=prop.unit, values=np.array(arr)
            )
    return properties


def get_reactor_property_values_by_reactor_id(
    reactor_id: int, session: Union[scoped_session, Session]
) -> Dict[str, PropertyValues]:
    properties = {}
    for prop_id in (
        session.query(CSSTReactorPropertyValues.csst_property_id)
        .filter_by(csst_reactor_id=reactor_id)
        .distinct()
    ):
        prop = session.query(CSSTProperty).filter_by(id=prop_id[0]).first()
        values = (
            session.query(CSSTReactorPropertyValues)
            .filter_by(csst_reactor_id=reactor_id, csst_property_id=prop.id)
            .all()
        )
        values = {value.array_index: value.value for value in values}
        arr = []
        for i in range(len(values)):
            arr.append(values[i])
        properties[prop.name] = PropertyValues(
            name=prop.name, unit=prop.unit, values=np.array(arr)
        )
    return properties


def get_csst_experiment(
    experiment: Experiment, session: Union[scoped_session, Session]
) -> CSSTExperiment:
    query = session.query(CSSTExperiment).filter_by(
        **remove_keys_with_null_values_in_dict(experiment.dict())
    )
    raise_lookup_error_if_query_count_is_not_one(query, "experiment", experiment.dict())
    exp = query.first()
    return exp


def get_csst_temperature_program(
    temperature_program: TemperatureProgram, session: Union[scoped_session, Session]
) -> CSSTTemperatureProgram:
    query = session.query(CSSTTemperatureProgram).filter(
        CSSTTemperatureProgram.hash == temperature_program.hash()
    )
    raise_lookup_error_if_query_count_is_not_one(
        query, "temperature program", temperature_program.hash()
    )
    temp_program = query.first()
    return temp_program


def get_lab_polymer_by_name(
    name: str, session: Union[scoped_session, Session]
) -> LabPolymer:
    lab_pols = session.query(LabPolymer).filter(LabPolymer.name == name).all()
    lab_pol_names = {pol.name: pol for pol in lab_pols}
    if len(lab_pol_names) == len(lab_pols) and name in lab_pol_names:
        return lab_pol_names[name]

    # TODO original method to extract brettmann polymer. Works if there aren't
    # any duplicate polymers
    raise_lookup_error_if_list_count_is_not_one(
        list(lab_pols), "lab polymer", {name: [pol.name for pol in lab_pols]}
    )
    return lab_pols[0]


def get_lab_solvent_by_name(
    name: str, session: Union[scoped_session, Session]
) -> LabSolvent:
    lab_sols = session.query(LabSolvent).filter(LabSolvent.name == name).all()
    raise_lookup_error_if_list_count_is_not_one(
        list(lab_sols), "lab solvent", {name: [sol.name for sol in lab_sols]}
    )
    return lab_sols[0]


def raise_lookup_error_if_query_count_is_not_one(query: Query, item: str, data: str):
    """Raises LookupError if query count is not one.
    Assumes the function call is nested in active Session or scoped_session

    Typical usage example:

        with Session() as session:
            query = ...
            raise_lookup_error_if_query_count_is_not_one(query)

    Args:
        query: query to check
        item: item being queried
        data: data used to query the item
    """
    if query.count() > 1:
        msg = (
            f"Multiple {item}s associated with {data}. "
            + "Make sure the database is correct."
        )
        logger.warning(msg)
        raise LookupError(msg)
    if query.count() < 1:
        msg = f"No {item} associated with {data}. " + f"Add the {item} first."
        logger.warning(msg)
        raise LookupError(msg)


def raise_lookup_error_if_list_count_is_not_one(li: List, item: str, data: str):
    """Raises LookupError if list is not size one

    Args:
        li: List to check
        item: item being queried
        data: data used to query the item
    """
    if len(li) > 1:
        msg = (
            f"Multiple {item}s associated with {data}. "
            + "Make sure the database is correct."
        )
        logger.warning(msg)
        raise LookupError(msg)
    if len(li) < 1:
        msg = f"No {item} associated with {data}. Add the {item} first."
        logger.warning(msg)
        raise LookupError(msg)


def get_property_id(prop_data, session: Union[scoped_session, Session]) -> int:
    return session.query(CSSTProperty).filter_by(**prop_data).first().id
