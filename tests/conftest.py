from pathlib import Path
import os

import pytest

try:
    from csst.experiment import _db
    from sqlalchemy_utils import database_exists, create_database, drop_database
except ImportError:
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
    )
    from pinrex.db import Base

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
        seed_database(session)
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
            {"id": 10000, "version": "test"}  # make id large so clash doesn't occur
        ]
        for exp in experiments:
            session.add(CSSTExperiment(**exp))
        session.commit()

        temp_programs = [
            {
                "id": 10000,  # make id large so clash doesn't occur
                "block": "test",
                "solvent_tune": [{}],
                "sample_load": [{}],
                "experiment": [{}],
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
                "conc": 0,
                "conc_unit": "test",
            }
        ]
        for reactor in reactors:
            session.add(CSSTReactor(**reactor))
        session.commit()
