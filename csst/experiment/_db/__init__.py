"""Optional interface for importing data from and exporting data to a database"""
from typing import Union
import logging

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session

from csst.experiment import Experiment
from csst.experiment._db import adder
from csst.experiment._db import getter

logger = logging.getLogger(__name__)


def add_experiment(experiment: Experiment, Session: Union[scoped_session, Session]):
    """Adds experiment data, temperature_program, and reactor data to database

    Args:
        experiment: experiment to add to table
        Session: session connected to the database
    """
    adder.add_experiment(experiment=experiment, Session=Session)
    adder.add_temperature_program(
        temperature_program=experiment.temperature_program, Session=Session
    )
    adder.add_experiment_reactors(experiment=experiment, Session=Session)
