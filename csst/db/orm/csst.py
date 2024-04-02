from sqlalchemy import Column, Integer, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import ARRAY

from csst.db._base import Base


class CSSTExperiment(Base):
    """Crystal 16 Dissolition/Solubility Test Experiment model

    Attributes:
        file_name (str): Original filename of the experiment. Note, this file may no
            longer exist or may be named differently.
        version (str): version of the data file.
        experiment_details (str): details about the experiment.
        experiment_number (str): experiment number.
        experimenter (str): Person who did the experiment.
        project (str): project name.
        lab_journal (str): information from the lab journal row.
        description (str): description of the experiment
        start_of_experiment (datetime): time the experiment was started
    """

    __tablename__ = "csst_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(Text)
    version = Column(Text, nullable=False)
    experiment_details = Column(Text)
    experiment_number = Column(Text)
    experimenter = Column(Text)
    project = Column(Text)
    lab_journal = Column(Text)
    description = Column(Text)
    start_of_experiment = Column(DateTime)


class CSSTTemperatureProgram(Base):
    """

    Attributes:
        block (str):
        solvent_tune: array of json of solvent tuning stage
        sample_load: array of json of sample loading stage
        experiment: array of json of experiment stage
        hash: hash to compare temperature programs with for equality
    """

    __tablename__ = "csst_temperature_programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    block = Column(Text, nullable=False)
    solvent_tune = Column(ARRAY(JSON, dimensions=1), nullable=False)
    sample_load = Column(ARRAY(JSON, dimensions=1), nullable=False)
    experiment = Column(ARRAY(JSON, dimensions=1), nullable=False)
    hash = Column(Text, nullable=False)


class CSSTReactor(Base):
    """Crystal 16 reactor model

    Attributes:
        lab_sol_id (int): solvent id of the solvent sample the lab tested
        lab_pol_id (int): polymer id of the polymer sample the lab tested
        conc (float): concentration of polymer in solvent
        conc_unit (str): unit of concentration
        csst_temperature_program_id (int): temperature program id
        csst_experiment_id (int): id of the experiment the reactor comes from
        reactor_number (int): the number reactor used
    """

    __tablename__ = "csst_reactors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_sol_id = Column(Integer, ForeignKey("lab_solvents.id"), nullable=False)
    lab_pol_id = Column(Integer, ForeignKey("lab_polymers.id"), nullable=False)
    conc = Column(Float, nullable=False)
    conc_unit = Column(Text, nullable=False)
    csst_temperature_program_id = Column(
        Integer, ForeignKey("csst_temperature_programs.id"), nullable=False
    )
    csst_experiment_id = Column(
        Integer, ForeignKey("csst_experiments.id"), nullable=False
    )
    reactor_number = Column(Integer, nullable=False)


class CSSTProperty(Base):
    """Model to store CSST reactor property information

    Attributes:
        name (str):
            Name of the property
        unit (str):
            Unit of the property
    """

    __tablename__ = "csst_properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    unit = Column(Text)


class CSSTReactorPropertyValues(Base):
    """Model to store CSST list of values for reactor property information
    like transmission

    Attributes:
        csst_property_id (int):
            Id in the CSSTProperty table
        csst_reactor_id (int):
            Id of the reactor the property is associated with
        array_index (int):
            Index of the property value in the original array
        values (float):
            Value of the property
    """

    __tablename__ = "csst_reactor_property_multiple_values"

    csst_property_id = Column(
        Integer, ForeignKey("csst_properties.id"), nullable=False, primary_key=True
    )
    csst_reactor_id = Column(
        Integer, ForeignKey("csst_reactors.id"), nullable=False, primary_key=True
    )
    array_index = Column(Integer, nullable=False, primary_key=True)
    value = Column(Float, nullable=False, primary_key=True)


class CSSTExperimentPropertyValue(Base):
    """Model to store CSST single value property information

    Attributes:
        csst_property_id (int):
            Id of the property in the CSSTProperty table the value represents
        csst_experiment_id (int):
            Id of the experiment the property is associated with
        value (float):
            Value of the property
    """

    __tablename__ = "csst_experiment_property_single_values"

    csst_property_id = Column(
        Integer, ForeignKey("csst_properties.id"), nullable=False, primary_key=True
    )
    csst_experiment_id = Column(
        Integer, ForeignKey("csst_experiments.id"), nullable=False, primary_key=True
    )
    value = Column(Float, nullable=False, primary_key=True)


class CSSTExperimentPropertyValues(Base):
    """Model to store CSST list of values for experiment property information
    like temperature and time

    Attributes:
        csst_property_id (int):
            Id in the CSSTProperty table
        csst_reactor_id (int):
            Id of the reactor the property is associated with
        array_index (int):
            Index of the property value in the original array
        values (float):
            Value of the property
    """

    __tablename__ = "csst_experiment_property_multiple_values"

    csst_property_id = Column(
        Integer, ForeignKey("csst_properties.id"), nullable=False, primary_key=True
    )
    csst_experiment_id = Column(
        Integer, ForeignKey("csst_experiments.id"), nullable=False, primary_key=True
    )
    array_index = Column(Integer, nullable=False, primary_key=True)
    value = Column(Float, nullable=False, primary_key=True)


class CSSTReactorProcessedTemperature(Base):
    """Model to store processed csst temperature data.
    See https://github.com/jdkern11/csst_analyzer/blob/main/csst/processor/models.py

    Attributes:
        csst_reactor_id (int):
            Id of the reactor the processed temperature is associated with
        average_temperature (float):
            Average temperature the solubility was processed at
        temperature_range (float):
             Range of temperatures around the average
        average_transmission (float):
            Average transmission at average_temperature +- (temperature_range / 2)
        median_transmission (float):
            Median transmission at average_temperature +- (temperature_range / 2)
        transmission_std (float):
            standard deviation of transmission at average_temperature +- (temperature_range / 2)
        heating: 1 if temp was analyzed in the heating state, 0 otherwise
        cooling: 1 if temp was analyzed in the cooling state, 0 otherwise
        holding: 1 if temp was analyzed in the holding state, 0 otherwise
        filtered: if the transmission data was filtered before processing
    """

    __tablename__ = "csst_reactor_processed_temperature_values"

    csst_reactor_id = Column(
        Integer, ForeignKey("csst_reactors.id"), nullable=False, primary_key=True
    )
    average_temperature = Column(Float, nullable=False, primary_key=True)
    temperature_range = Column(Float, nullable=False, primary_key=True)
    average_transmission = Column(Float, nullable=False)
    median_transmission = Column(Float, nullable=False)
    transmission_std = Column(Float, nullable=False)
    heating = Column(Integer, nullable=False, primary_key=True)
    cooling = Column(Integer, nullable=False, primary_key=True)
    holding = Column(Integer, nullable=False, primary_key=True)
    filtered = Column(Boolean, nullable=False, primary_key=True)
