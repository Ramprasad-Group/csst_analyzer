"""Optional interface for importing data from and exporting data to a database"""
from typing import Union
import logging

from sqlalchemy import cast, String
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from pinrex.db.helpers import make_name_searchable
from pinrex.db.models.polymer import Polymer, PolymerName
from pinrex.db.models.solvent import Solvent, SolventName
from pinrex.db.models.lab import BrettmannLabPolymer, BrettmannLabSolvent
from pinrex.db.models.csst import (
    CSSTExperiment,
    CSSTTemperatureProgram,
    CSSTReactor,
    CSSTProperty,
    CSSTReactorPropertyValue,
    CSSTReactorPropertyValues
)

from csst.experiment import Experiment

logger = logging.getLogger(__name__)

def add_experiment(
    experiment: Experiment,
    Session: Union[scoped_session, Session]
):
    """Adds experiment data, temperature_program, and reactor data to database

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    _add_experiment(experiment=experiment, Session=Session)

def _add_experiment(
    experiment: Experiment,
    Session: Union[scoped_session, Session]
):
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
        else:
            data["file_name"] = experiment.file_name
            logger.info(f"Adding CSST Experiment {data} to the database")
            session.add(CSSTExperiment(**data))
            session.commit()

def _add_temperature_program(
    experiment: Experiment,
    Session: Union[scoped_session, Session]
):
    """Adds temperature program to the temperature program table

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    data = experiment.temperature_program.dict()
    hash_ = experiment.temperature_program.hash()
    data['hash'] = hash_
    logger.info(f"Searching for {data} in CSSTTemperatureProgram table")
    with Session() as session:
        if (
            session.query(CSSTTemperatureProgram)
            .filter(CSSTTemperatureProgram.hash == hash_)
        ).count() > 0:
            logger.info(f"{data} already added")
        else:
            logger.info(f"Adding CSST Temperature Program {data} to the database")
            session.add(CSSTTemperatureProgram(**data))
            session.commit()
