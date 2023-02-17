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
    csste.experiment_details = "example experiment details"
    csste.experiment_number = "0"
    csste.experimenter = "tester"
    csste.project = "example data version 1014"
    csste.lab_journal = None
    csste.description = "test"
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
    temp = [5, 5, 10, 10, 15, 15, 20, 20, 20, 20]
    trans = [5, 4, 20, 22, 50, 45, 78, 78, 79, 80]
    """
    time = PropertyValues(name="time", unit="hours", values=np.linspace(0, 1, num=10))
    temp = [5, 10, 15, 20, 20, 20, 20, 15, 10, 5]
    actual_temperature = PropertyValues(
        name="temperature", unit="C", values=np.array(temp)
    )
    trans = [5, 20, 50, 78, 79, 80, 78, 45, 22, 4]
    transmission = PropertyValues(name="transmission", unit="%", values=np.array(trans))
    return Reactor.construct(
        solvent=None,
        polymer=None,
        conc=None,
        temperature_program=None,
        set_temperature=None,
        stir_rates=None,
        bottom_stir_rate=None,
        transmission=transmission,
        actual_temperature=actual_temperature,
        time_since_experiment_start=time,
    )
