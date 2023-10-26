"""Optional interface for importing data from and exporting data to a database"""
from typing import Union, List, Optional
import logging
from datetime import datetime

from csst.experiment import Experiment
from csst.db import adder, getter

logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm.scoping import scoped_session
    from sqlalchemy.orm.session import Session
except ModuleNotFoundError:
    msg = (
        "This subpackage can only be used if the optional database dependencies "
        + "are installed and the database connection set up. Use "
        + "`poetry install --with db` to install the dependencies and see the GitHub"
        + " page for information on the database connection"
    )
    logger.warning(msg)
    raise ModuleNotFoundError(msg)


def add_experiment(experiment: Experiment, session: Union[scoped_session, Session]):
    """Adds experiment data, temperature_program, and reactor data to database

    Args:
        experiment: experiment to add to table
        session: instantiated session connected to the database
    """
    exp_id = adder.add_experiment_and_or_get_id(experiment=experiment, session=session)
    temp_program_id = adder.add_temperature_program_and_or_get_program_id(
        temperature_program=experiment.temperature_program, session=session
    )
    adder.add_experiment_reactors(
        experiment=experiment,
        experiment_id=exp_id,
        temperature_program_id=temp_program_id,
        session=session,
    )


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
    return getter.get_experiments(experiment, session)
