from pathlib import Path
from datetime import datetime
import os

import pytest

try:
    from csst import db
    from sqlalchemy_utils import database_exists, create_database, drop_database
except ImportError as e:
    _db_option = False
else:
    _db_option = True

# don't want to ignore import errors here
if _db_option:
    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sshtunnel import SSHTunnelForwarder
    from pinrex.db.helpers import make_name_searchable
    from pinrex.db.models.polymer import Polymer, PolymerName
    from pinrex.db.models.solvent import Solvent, SolventName
    from pinrex.db.models.lab import BrettmannLabPolymer, BrettmannLabSolvent
    from pinrex.db.models.csst import (
        CSSTExperiment,
        CSSTTemperatureProgram,
        CSSTReactor,
        CSSTProperty,
        CSSTExperimentPropertyValue,
        CSSTReactorPropertyValues,
        CSSTExperimentPropertyValues,
    )
    from pinrex.db import Base
    from csst.experiment.models import (
        PropertyNameEnum,
        TemperatureSettingEnum,
        TemperatureChange,
        PropertyValue,
    )

if _db_option:

    @pytest.fixture(scope="module")
    def server():
        """SSH server to connect to the database through"""
        dotenv_path = Path(__file__).parent.absolute() / ".." / ".env"
        if not dotenv_path.exists():
            raise FileNotFoundError(
                ".env file must be created in the source folder with CSST_DB_USER, "
                + "CSST_DB_PASSWORD, CSST_DB_HOST, CSST_DB_PORT, CSST_DB_NAME, "
                + "SSH_TUNNEL_HOST, SSH_TUNNEL_PORT, SSH_USERNAME, and SSH_PASSWORD "
                + "set."
            )
        load_dotenv(str(dotenv_path))
        server = SSHTunnelForwarder(
            (os.environ.get("SSH_TUNNEL_HOST"), int(os.environ.get("SSH_TUNNEL_PORT"))),
            ssh_username=os.environ.get("SSH_USERNAME"),
            ssh_password=os.environ.get("SSH_PASSWORD"),
            remote_bind_address=(
                os.environ.get("CSST_DB_HOST"),
                int(os.environ.get("CSST_DB_PORT")),
            ),
        )
        server.start()
        yield server
        server.stop()

    @pytest.fixture(scope="module")
    def engine(server):
        db_server = "postgresql+psycopg2://{}:{}@{}:{}/{}_test".format(
            os.environ.get("CSST_DB_USER"),
            os.environ.get("CSST_DB_PASSWORD"),
            os.environ.get("CSST_DB_HOST"),
            server.local_bind_port,
            os.environ.get("CSST_DB_NAME"),
        )
        engine = create_engine(db_server)
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            raise FileExistsError(
                "Database already exists. Since the database is "
                + "dropped at the end of testing, stopping the test."
            )
        yield engine

        drop_database(engine.url)

    @pytest.fixture(scope="module")
    def setup_database(engine):
        Base.metadata.create_all(engine)

        yield

        Base.metadata.drop_all(engine)

    @pytest.fixture(scope="function")
    def session(engine, setup_database):
        connection = engine.connect()
        transaction = connection.begin()
        session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=connection)
        )
        try:
            seed_database(session)
        except Exception as e:
            print(e)
            transaction.rollback()
            return
        yield session
        transaction.rollback()

    def seed_database(session):
        """Seeds database with items used during database testing

        Note, if an id is set, no new items can be added without throwing an error
        if the id of the new item == the set id. Indexing starts at 1, so if the id
        is large it likely won't be reached. If the id is small, it assumes that
        no new items will be added.
        """
        # polymers are PEG, PEO and PVP
        # solvent is MeOH
        polymers = [
            {
                "id": 1,
                "smiles": "[*]CCO[*]",
                "fingerprint": {"temp": 1},
                "category": "known",
                "canonical_smiles": "[*]CCO[*]",
            },
            {
                "id": 2,
                "smiles": "[*]CC([*])N1CCCC1=O",
                "fingerprint": {"temp": 1},
                "category": "known",
                "canonical_smiles": "[*]CC([*])N1CCCC1=O",
            },
        ]
        for polymer in polymers:
            session.add(Polymer(**polymer))
        session.commit()

        solvents = [
            {"id": 1, "smiles": "CO", "fingerprint": {"temp": 1}},
        ]
        for solvent in solvents:
            session.add(Solvent(**solvent))
        session.commit()

        polymer_names = [
            {
                "pol_id": 1,
                "name": "PEG",
                "search_name": make_name_searchable("PEG"),
                "naming_convention": "abbreviation",
            },
            {
                "pol_id": 1,
                "name": "PEO",
                "search_name": make_name_searchable("PEO"),
                "naming_convention": "abbreviation",
            },
            {
                "pol_id": 2,
                "name": "PVP",
                "search_name": make_name_searchable("PVP"),
                "naming_convention": "abbreviation",
            },
        ]
        for polymer in polymer_names:
            session.add(PolymerName(**polymer))
        session.commit()

        solvent_names = [
            {
                "sol_id": 1,
                "name": "MeOH",
                "search_name": make_name_searchable("MeOH"),
                "naming_convention": "abbreviation",
            },
            {
                "sol_id": 1,
                "name": "methanol",
                "search_name": make_name_searchable("methanol"),
                "naming_convention": "standard",
            },
        ]
        for solvent in solvent_names:
            session.add(SolventName(**solvent))
        session.commit()

        lab_solvents = [
            {"id": 1, "sol_id": 1, "name": "methanol", "percent_purity": 99}
        ]

        for solvent in lab_solvents:
            session.add(BrettmannLabSolvent(**solvent))
        session.commit()

        lab_polymers = [
            {
                "id": 1,
                "pol_id": 1,
                "name": "PEG",
                "number_average_mw_min": 9000,
                "number_average_mw_max": 10000,
                "supplier": "thermofischer",
            },
            {
                "id": 2,
                "pol_id": 2,
                "name": "PVP",
                "number_average_mw_min": 11000,
                "number_average_mw_max": 11000,
                "supplier": "thermofischer",
            },
        ]
        for polymer in lab_polymers:
            session.add(BrettmannLabPolymer(**polymer))
        session.commit()

        experiments = [
            {
                "id": 10000,  # make id large so clash doesn't occur
                "version": "test",
                "file_name": "test1.csv",
                "experiment_details": "test",
                "experiment_number": "test",
                "experimenter": "test",
                "project": "test",
                "lab_journal": "test",
                "description": "test",
                "start_of_experiment": datetime(year=1996, month=5, day=11),
            },
            {
                "id": 10001,  # make id large so clash doesn't occur
                "version": "test",
                "file_name": "test2.csv",
                "experiment_details": None,
                "experiment_number": None,
                "experimenter": "Joe",
                "project": "test",
                "lab_journal": "test",
                "description": "test",
                "start_of_experiment": datetime(year=1996, month=5, day=12),
            },
        ]
        for exp in experiments:
            session.add(CSSTExperiment(**exp))
        session.commit()

        default_step = TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=20, unit="°C"),
            rate=PropertyValue(name="temperature_change_rate", value=20, unit="°C/min"),
        )

        temp_programs = [
            {
                "id": 10000,  # make id large so clash doesn't occur
                "block": "test",
                "solvent_tune": [default_step.dict()],
                "sample_load": [default_step.dict()],
                "experiment": [default_step.dict()],
                "hash": "test",
            }
        ]
        for temp_program in temp_programs:
            session.add(CSSTTemperatureProgram(**temp_program))
        session.commit()

        reactors = [
            {
                "id": 10000,  # set to large number so clash doesn't occur
                "bret_sol_id": 1,
                "bret_pol_id": 1,
                "csst_temperature_program_id": 10000,
                "csst_experiment_id": 10000,
                "conc": 5,
                "conc_unit": "test",
                "reactor_number": 1
            },
            {
                "id": 10001,  # set to large number so clash doesn't occur
                "bret_sol_id": 1,
                "bret_pol_id": 1,
                "csst_temperature_program_id": 10000,
                "csst_experiment_id": 10000,
                "conc": 10,
                "conc_unit": "test",
                "reactor_number": 1
            },
            {
                "id": 10002,  # set to large number so clash doesn't occur
                "bret_sol_id": 1,
                "bret_pol_id": 2,
                "csst_temperature_program_id": 10000,
                "csst_experiment_id": 10000,
                "conc": 15,
                "conc_unit": "test",
                "reactor_number": 1
            },
            {
                "id": 10003,  # set to large number so clash doesn't occur
                "bret_sol_id": 1,
                "bret_pol_id": 1,
                "csst_temperature_program_id": 10000,
                "csst_experiment_id": 10001,
                "conc": 5,
                "conc_unit": "test",
                "reactor_number": 1
            },
        ]
        for reactor in reactors:
            session.add(CSSTReactor(**reactor))
        session.commit()
        multi_reactor_properties = [
            {"name": PropertyNameEnum.TRANS, "unit": "test"},
        ]
        for prop in multi_reactor_properties:
            session.add(CSSTProperty(**prop))
        session.commit()

        # add fake data for every reactor
        for i in range(10000, 10004):
            # add 10 datapoints for each offset by 10 for each reactor based on reactor id
            for prop in multi_reactor_properties:
                prop_id = session.query(CSSTProperty).filter_by(**prop).first().id
                ind = 0
                for j in range(i * 10, i * 10 + 10):
                    session.add(
                        CSSTReactorPropertyValues(
                            csst_reactor_id=i,
                            csst_property_id=prop_id,
                            value=j,
                            array_index=ind,
                        )
                    )
                    ind += 1

        single_experiment_properties = [
            {"name": PropertyNameEnum.BOTTOM_STIR_RATE, "unit": "test"},
        ]
        multi_experiment_properties = [
            {"name": PropertyNameEnum.TEMP, "unit": "test"},
            {"name": PropertyNameEnum.STIR_RATE, "unit": "test"},
            {"name": PropertyNameEnum.TIME, "unit": "test"},
            {"name": "set_temperature", "unit": "test"},
        ]
        for prop in single_experiment_properties:
            session.add(CSSTProperty(**prop))
        for prop in multi_experiment_properties:
            session.add(CSSTProperty(**prop))
        session.commit()

        # add fake data for every experiment
        for i in range(10000, 10002):
            for prop in single_experiment_properties:
                prop_id = session.query(CSSTProperty).filter_by(**prop).first().id
                session.add(
                    CSSTExperimentPropertyValue(
                        csst_experiment_id=i, csst_property_id=prop_id, value=i
                    )
                )
            for prop in multi_experiment_properties:
                prop_id = session.query(CSSTProperty).filter_by(**prop).first().id
                ind = 0
                for j in range(i * 10, i * 10 + 10):
                    session.add(
                        CSSTExperimentPropertyValues(
                            csst_experiment_id=i,
                            csst_property_id=prop_id,
                            value=j,
                            array_index=ind,
                        )
                    )
                    ind += 1

        session.commit()
