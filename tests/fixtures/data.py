from pathlib import Path
import datetime

import pandas as pd
import numpy as np
import pytest

from csst.analyzer import Analyzer
from csst.analyzer.models import (
    TemperatureProgram,
    TemperatureHold,
    TemperatureChange,
    TemperatureSettingEnum,
    PropertyValue
)


@pytest.fixture
def cssta_1014():
    cssta = Analyzer.load_from_file(
        str(Path(__file__).parent.absolute() / ".." / "test_data" / "example_data_version_1014.csv")
    )
    return cssta

@pytest.fixture
def manual_1014():
    """Manually reading of 1014 example data"""
    cssta = Analyzer()
    cssta.experiment_details = 'example experiment details'
    cssta.experiment_number = '0'
    cssta.experimenter = 'tester'
    cssta.project = 'example data version 1014'
    cssta.lab_journal = None
    cssta.description = 'test'
    cssta.start_of_experiment = datetime.datetime(
        year=2022, month=8, day=19, hour=13, minute=54
    )
    cssta.bottom_stir_rate = PropertyValue(
        name = 'bottom_stir_rate',
        value = 900,
        unit = 'rpm'
    )

    # test temperature program loading
    tuning = [
        TemperatureChange(
            setting = TemperatureSettingEnum.HEAT,
            to = PropertyValue(
                name = 'temperature',
                value = 20,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 20,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 20,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 26,
                unit = 'sec'
            )
        )
    ]
    sample_load = [
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 20,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 249,
                unit = 'sec'
            )
        )
    ]
    experiment = [
        TemperatureChange(
            setting = TemperatureSettingEnum.HEAT,
            to = PropertyValue(
                name = 'temperature',
                value = 60,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 0.5,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 60,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 3541,
                unit = 'sec'
            )
        ),
        TemperatureChange(
            setting = TemperatureSettingEnum.COOL,
            to = PropertyValue(
                name = 'temperature',
                value = 10,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 0.5,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 10,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 7201,
                unit = 'sec'
            )
        ),
        TemperatureChange(
            setting = TemperatureSettingEnum.HEAT,
            to = PropertyValue(
                name = 'temperature',
                value = 60,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 0.5,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 60,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 3541,
                unit = 'sec'
            )
        ),
        TemperatureChange(
            setting = TemperatureSettingEnum.COOL,
            to = PropertyValue(
                name = 'temperature',
                value = 10,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 0.5,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 10,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 7201,
                unit = 'sec'
            )
        ),
        TemperatureChange(
            setting = TemperatureSettingEnum.HEAT,
            to = PropertyValue(
                name = 'temperature',
                value = 25,
                unit = '°C'
            ),
            rate = PropertyValue(
                name = 'temperature_change_rate',
                value = 0.5,
                unit = '°C/min'
            )
        ),
        TemperatureHold(
            at = PropertyValue(
                name = 'temperature',
                value = 25,
                unit = '°C'
            ),
            for_ = PropertyValue(
                name = 'time',
                value = 3541,
                unit = 'sec'
            )
        ),
    ]
    cssta.temperature_program = TemperatureProgram(
        block = 'A',
        solvent_tune = tuning,
        sample_load = sample_load,
        experiment = experiment
    )
    return cssta

@pytest.fixture
def test_cssta(cssta_1014):
    """Convert cssta_obj dataframe reactor data

    Reactor1 data will be simple be the actual temp

    Reactor2 data will be the actual temp squared

    Reactor3 data will be the log of the absolute value of the actual temp + 1
    """
    temp_col = [col for col in cssta_obj.df.columns if "Temperature Actual" in col][0]
    reactor_cols = [
        col
        for col in cssta_obj.df.columns
        for reactor in cssta_obj.samples.keys()
        if reactor in col
    ]
    for col in reactor_cols:
        if "Reactor1" in col:
            fake_data = cssta_obj.df[temp_col].to_list()
            cssta_obj.df[col] = fake_data.copy()
        if "Reactor2" in col:
            fake_data = [t**2 for t in cssta_obj.df[temp_col].to_list()]
            cssta_obj.df[col] = fake_data.copy()
        if "Reactor3" in col:
            fake_data = [np.log(abs(t) + 1) for t in cssta_obj.df[temp_col].to_list()]
            cssta_obj.df[col] = fake_data.copy()
    return cssta_obj
