from pathlib import Path
import datetime

import pandas as pd
import numpy as np
import pytest

from csst.experiment import Experiment
from csst.experiment.models import (
    Reactor,
    TemperatureProgram,
    TemperatureHold,
    TemperatureChange,
    TemperatureSettingEnum,
    PropertyValue,
    PropertyValues,
)


@pytest.fixture
def csste_1014():
    csste = Experiment.load_from_file(
        str(
            Path(__file__).parent.absolute()
            / ".."
            / "test_data"
            / "example_data_version_1014.csv"
        )
    )
    return csste


@pytest.fixture
def manual_1014():
    """Manually reading of 1014 example data"""
    csste = Experiment()
    csste.version = "test"
    csste.file_name = "example_data_version_1014.csv"
    csste.experiment_details = "example experiment details"
    csste.experiment_number = "0"
    csste.experimenter = "tester"
    csste.project = "example data version 1014"
    csste.lab_journal = None
    csste.description = [
        "test",
        "polymer_ids,PEG:34,PEO:46,PVP:41",
        "solvent_ids,1,2dichlorobenzene:37,Ethyl Acetate:19,MeOH:3",
        "CAS: ###-##-#",
        "density:0.##",
        "Different concentratin of # - ## - ### mg/ mL  is being tested along with temprature going from 10-60 C",
        "Temp ramp rate: 0.5 C/min",
        "Mixing speed: 900 RPM",
        "Hold time: 1 hr(hot)-2hrs (cold)",
    ]
    csste.start_of_experiment = datetime.datetime(
        year=2022, month=8, day=19, hour=13, minute=54
    )
    csste.bottom_stir_rate = PropertyValue(
        name="bottom_stir_rate", value=900, unit="rpm"
    )

    # test temperature program loading
    tuning = [
        TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=20, unit="°C"),
            rate=PropertyValue(name="temperature_change_rate", value=20, unit="°C/min"),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=20, unit="°C"),
            for_=PropertyValue(name="time", value=26, unit="sec"),
        ),
    ]
    sample_load = [
        TemperatureHold(
            at=PropertyValue(name="temperature", value=20, unit="°C"),
            for_=PropertyValue(name="time", value=249, unit="sec"),
        )
    ]
    experiment = [
        TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=60, unit="°C"),
            rate=PropertyValue(
                name="temperature_change_rate", value=0.5, unit="°C/min"
            ),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=60, unit="°C"),
            for_=PropertyValue(name="time", value=3541, unit="sec"),
        ),
        TemperatureChange(
            setting=TemperatureSettingEnum.COOL,
            to=PropertyValue(name="temperature", value=10, unit="°C"),
            rate=PropertyValue(
                name="temperature_change_rate", value=0.5, unit="°C/min"
            ),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=10, unit="°C"),
            for_=PropertyValue(name="time", value=7201, unit="sec"),
        ),
        TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=60, unit="°C"),
            rate=PropertyValue(
                name="temperature_change_rate", value=0.5, unit="°C/min"
            ),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=60, unit="°C"),
            for_=PropertyValue(name="time", value=3541, unit="sec"),
        ),
        TemperatureChange(
            setting=TemperatureSettingEnum.COOL,
            to=PropertyValue(name="temperature", value=10, unit="°C"),
            rate=PropertyValue(
                name="temperature_change_rate", value=0.5, unit="°C/min"
            ),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=10, unit="°C"),
            for_=PropertyValue(name="time", value=7201, unit="sec"),
        ),
        TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=25, unit="°C"),
            rate=PropertyValue(
                name="temperature_change_rate", value=0.5, unit="°C/min"
            ),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=25, unit="°C"),
            for_=PropertyValue(name="time", value=3541, unit="sec"),
        ),
    ]
    csste.temperature_program = TemperatureProgram(
        block="A", solvent_tune=tuning, sample_load=sample_load, experiment=experiment
    )
    return csste


@pytest.fixture
def reactor():
    """Handcrafted reactor for testing

    reactor values sorted by temp would be
    temp = [0, 0, 0, 0, 5, 5, 10, 10, 15, 15, 20, 20, 20, 20]
    trans = [0, 0, 0, 0, 5, 4, 20, 22, 50, 45, 78, 78, 79, 80]
    """
    time = PropertyValues(name="time", unit="hours", values=np.linspace(0, 1.4, num=14))
    temp = [0, 0, 0, 0, 5, 10, 15, 20, 20, 20, 20, 15, 10, 5]
    actual_temperature = PropertyValues(
        name="temperature", unit="C", values=np.array(temp)
    )
    trans = [0, 0, 0, 0, 5, 20, 50, 78, 79, 80, 78, 45, 22, 4]
    transmission = PropertyValues(name="transmission", unit="%", values=np.array(trans))
    stir = [0 for i in trans]
    stirs = PropertyValues(name="stir_rate", unit="rpm", values=np.array(stir))
    tuning = [
        TemperatureChange(
            setting=TemperatureSettingEnum.HEAT,
            to=PropertyValue(name="temperature", value=20, unit="°C"),
            rate=PropertyValue(name="temperature_change_rate", value=20, unit="°C/min"),
        ),
        TemperatureHold(
            at=PropertyValue(name="temperature", value=20, unit="°C"),
            for_=PropertyValue(name="time", value=360, unit="sec"),
        ),
    ]
    sample_load = [
        TemperatureHold(
            at=PropertyValue(name="temperature", value=20, unit="°C"),
            for_=PropertyValue(name="time", value=720, unit="sec"),
        )
    ]
    temperature_program = TemperatureProgram(
        block="A", solvent_tune=tuning, sample_load=sample_load, experiment=[]
    )

    exp = Experiment()
    exp.temperature_program = temperature_program
    exp.set_temperature = actual_temperature
    exp.stir_rates = stirs
    exp.bottom_stir_rate = PropertyValue(name="bottom_stir_rate", value=900, unit="rpm")
    exp.actual_temperature = actual_temperature
    exp.time_since_experiment_start = time

    reactor = Reactor.construct(
        solvent="MeOH",
        polymer="PEG",
        solvent_id=3,
        reactor_number=1,
        conc=PropertyValue(name="concentration", value=5, unit="test_concentration"),
        transmission=transmission,
        experiment=exp,
    )
    return reactor
