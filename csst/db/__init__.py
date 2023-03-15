"""Optional interface for importing data from and exporting data to a database"""
from typing import Union, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm.scoping import scoped_session
    from sqlalchemy.orm.session import Session
except ModuleNotFoundError:
    msg = (
        f"This subpackage can only be used if the optional database dependencies "
        + "are installed and the database connection set up. Use "
        + "`poetry install --with db` to install the dependencies and see the GitHub"
        + " page for information on the database connection"
    )
    logger.warning(msg)
    raise ModuleNotFoundError(msg)


from csst.experiment import Experiment
from csst.db import adder, getter


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


def load_from_db(
    Session: Union[Session, scoped_session],
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
        Session: connected to the database.
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
    return get_experiments_from_experiment_details(obj, Session)


def get_experiments_from_experiment_details(
    experiment: Experiment, Session: Union[scoped_session, Session]
) -> List[Experiment]:
    """Gets a list of experiments that match the experiment metadata passed

    Args:
        experiment: experiment object that has any experiment details
        (values returned by experiment.dict()) filled out
        Session: session connected to the database
    """
    return getter.get_experiments(experiment, Session)
