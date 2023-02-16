from pathlib import Path
import datetime

import pandas as pd
import numpy as np
import pytest

from csst.experiment import Experiment
from csst.experiment.models import (
    TemperatureProgram,
    TemperatureHold,
    TemperatureChange,
    TemperatureSettingEnum,
    PropertyValue,
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
def test_csste(csste_1014):
    """Convert csste_obj dataframe reactor data

    Reactor1 data will be simple be the actual temp

    Reactor2 data will be the actual temp squared

    Reactor3 data will be the log of the absolute value of the actual temp + 1
    """
    temp_col = [col for col in csste_obj.df.columns if "Temperature Actual" in col][0]
    reactor_cols = [
        col
        for col in csste_obj.df.columns
        for reactor in csste_obj.samples.keys()
        if reactor in col
    ]
    for col in reactor_cols:
        if "Reactor1" in col:
            fake_data = csste_obj.df[temp_col].to_list()
            csste_obj.df[col] = fake_data.copy()
        if "Reactor2" in col:
            fake_data = [t**2 for t in csste_obj.df[temp_col].to_list()]
            csste_obj.df[col] = fake_data.copy()
        if "Reactor3" in col:
            fake_data = [np.log(abs(t) + 1) for t in csste_obj.df[temp_col].to_list()]
            csste_obj.df[col] = fake_data.copy()
    return csste_obj
