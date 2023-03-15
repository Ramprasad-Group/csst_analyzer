"""Functions for getting data from the database"""
from typing import Union, List
import logging

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from pinrex.db.helpers import make_name_searchable
from pinrex.db.models.polymer import Polymer, PolymerName
from pinrex.db.models.solvent import Solvent, SolventName
from pinrex.db.models.lab import BrettmannLabPolymer, BrettmannLabSolvent
from pinrex.db.models.csst import CSSTTemperatureProgram, CSSTExperiment

from csst.experiment import Experiment
from csst.experiment.models import TemperatureProgram

logger = logging.getLogger(__name__)


def get_experiment(
    experiment: Experiment, Session: Union[scoped_session, Session]
) -> CSSTExperiment:
    with Session() as session:
        query = session.query(CSSTExperiment).filter_by(**experiment.dict())
        raise_lookup_error_if_query_count_is_not_one(
            query, "experiment", experiment.dict()
        )
        exp = query.first()
    return exp


def get_temperature_program(
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
