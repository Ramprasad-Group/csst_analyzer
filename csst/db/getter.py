"""Functions for getting data from the database"""
from typing import Union, List, Dict
import logging

import numpy as np
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from pinrex.db.helpers import make_name_searchable
from pinrex.db.models.polymer import Polymer, PolymerName
from pinrex.db.models.solvent import Solvent, SolventName
from pinrex.db.models.lab import BrettmannLabPolymer, BrettmannLabSolvent
from pinrex.db.models.csst import (
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
from csst.experiment.models import TemperatureProgram, PropertyValue, PropertyValues

logger = logging.getLogger(__name__)


def get_experiments(
    experiment: Experiment, Session: Union[scoped_session, Session]
) -> List[Experiment]:
    """Gets all experiments associated with the experiment dict data"""
    experiments = []
    exps = get_csst_experiments(experiment, Session)
    if len(exps) == 0:
        return experiments
    for exp in exps:
        reactors = get_csst_reactors_by_experiment_id(exp.id, Session)
        temp_program = get_temperature_program_by_id(
            reactors[0].csst_temperature_program_id, Session
        )
        exp_value_properties = get_experiment_property_value_by_experiment_id(
            exp.id, Session
        )
        exp_values_properties = get_experiment_property_values_by_experiment_id(
            exp.id, Session
        )
        reactors = [
            (reactor, get_reactor_property_values_by_reactor_id(reactor.id, Session))
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
        experiment.bottom_stir_rate = exp_value_properties[
            PropertyNameEnum.BOTTOM_STIR_RATE
        ]
        experiment.set_temperature = exp_values_properties["set_temperature"]
        experiment.actual_temperature = exp_values_properties[PropertyNameEnum.TEMP]
        experiment.time_since_experiment_start = exp_values_properties[
            PropertyNameEnum.TIME
        ]
        experiment.stir_rates = exp_values_properties[PropertyNameEnum.STIR_RATE]
        experiment.reactors = [
            Reactor(
                solvent=get_lab_solvent_by_id(reactor.bret_sol_id, Session).name,
                polymer=get_lab_polymer_by_id(reactor.bret_pol_id, Session).name,
                conc=PropertyValue(
                    name=PropertyNameEnum.CONC,
                    unit=reactor.conc_unit,
                    value=reactor.conc,
                ),
                transmission=reactor_prop[PropertyNameEnum.TRANS],
                temperature_program=experiment.temperature_program,
                actual_temperature=experiment.actual_temperature,
                set_temperature=experiment.set_temperature,
                time_since_experiment_start=experiment.time_since_experiment_start,
                stir_rates=experiment.stir_rates,
                bottom_stir_rate=experiment.bottom_stir_rate,
            )
            for reactor, reactor_prop in reactors
        ]
        experiments.append(experiment)
    return experiments


def get_csst_experiments(
    experiment: Experiment, Session: Union[scoped_session, Session]
) -> List[CSSTExperiment]:
    with Session() as session:
        return (
            session.query(CSSTExperiment)
            .filter_by(**remove_keys_with_null_values_in_dict(experiment.dict()))
            .all()
        )


def get_csst_reactors_by_experiment_id(
    experiment_id: int, Session: Union[scoped_session, Session]
) -> List[CSSTReactor]:
    with Session() as session:
        return (
            session.query(CSSTReactor).filter_by(csst_experiment_id=experiment_id).all()
        )


def get_temperature_program_by_id(
    id_: int, Session: Union[scoped_session, Session]
) -> TemperatureProgram:
    with Session() as session:
        temp_program = session.query(CSSTTemperatureProgram).filter_by(id=id_).first()
    return TemperatureProgram(
        block=temp_program.block,
        solvent_tune=temp_program.solvent_tune,
        sample_load=temp_program.sample_load,
        experiment=temp_program.experiment,
    )


def get_lab_polymer_by_id(
    id_: int, Session: Union[scoped_session, Session]
) -> BrettmannLabPolymer:
    with Session() as session:
        return session.query(BrettmannLabPolymer).filter_by(id=id_).first()


def get_lab_solvent_by_id(
    id_: int, Session: Union[scoped_session, Session]
) -> BrettmannLabSolvent:
    with Session() as session:
        return session.query(BrettmannLabSolvent).filter_by(id=id_).first()


def get_experiment_property_value_by_experiment_id(
    experiment_id: int, Session: Union[scoped_session, Session]
) -> Dict[str, PropertyValue]:
    properties = {}
    with Session() as session:
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
    experiment_id: int, Session: Union[scoped_session, Session]
) -> Dict[str, PropertyValues]:
    properties = {}
    with Session() as session:
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
    reactor_id: int, Session: Union[scoped_session, Session]
) -> Dict[str, PropertyValues]:
    properties = {}
    with Session() as session:
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
    experiment: Experiment, Session: Union[scoped_session, Session]
) -> CSSTExperiment:
    with Session() as session:
        query = session.query(CSSTExperiment).filter_by(
            **remove_keys_with_null_values_in_dict(experiment.dict())
        )
        raise_lookup_error_if_query_count_is_not_one(
            query, "experiment", experiment.dict()
        )
        exp = query.first()
    return exp


def get_csst_temperature_program(
    temperature_program: TemperatureProgram, Session: Union[scoped_session, Session]
) -> CSSTTemperatureProgram:
    with Session() as session:
        query = session.query(CSSTTemperatureProgram).filter(
            CSSTTemperatureProgram.hash == temperature_program.hash()
        )
        raise_lookup_error_if_query_count_is_not_one(
            query, "temperature program", temperature_program.hash()
        )
        temp_program = query.first()
    return temp_program


def get_lab_polymer_by_name(
    name: str, Session: Union[scoped_session, Session]
) -> BrettmannLabPolymer:
    with Session() as session:
        pols = (
            session.query(PolymerName.pol_id)
            .filter(PolymerName.search_name == make_name_searchable(name))
            .distinct()
        )
        pol_ids = [pol.pol_id for pol in pols]
        lab_pols = (
            session.query(BrettmannLabPolymer)
            .filter(BrettmannLabPolymer.pol_id.in_(pol_ids))
            .all()
        )
        raise_lookup_error_if_list_count_is_not_one(
            list(lab_pols), "lab polymer", list(lab_pols)
        )
    return lab_pols[0]


def get_lab_solvent_by_name(
    name: str, Session: Union[scoped_session, Session]
) -> BrettmannLabSolvent:
    with Session() as session:
        sols = (
            session.query(SolventName.sol_id)
            .filter(SolventName.search_name == make_name_searchable(name))
            .distinct()
        )
        sol_ids = [sol.sol_id for sol in sols]
        lab_sols = (
            session.query(BrettmannLabSolvent)
            .filter(BrettmannLabSolvent.sol_id.in_(sol_ids))
            .all()
        )
        raise_lookup_error_if_list_count_is_not_one(
            list(lab_sols), "lab solvent", list(lab_sols)
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
            + f"Make sure the database is correct."
        )
        logger.warning(msg)
        raise LookupError(msg)
    if query.count() < 1:
        msg = f"No {item} associated with {data}. " + f"Add the {item} first."
        logger.warning(msg)
        raise LookupError(msg)


def raise_lookup_error_if_list_count_is_not_one(l: List, item: str, data: str):
    """Raises LookupError if list is not size one

    Args:
        l: List to check
        item: item being queried
        data: data used to query the item
    """
    if len(l) > 1:
        msg = (
            f"Multiple {item}s associated with {data}. "
            + f"Make sure the database is correct."
        )
        logger.warning(msg)
        raise LookupError(msg)
    if len(l) < 1:
        msg = f"No {item} associated with {data}. " + f"Add the {item} first."
        logger.warning(msg)
        raise LookupError(msg)
