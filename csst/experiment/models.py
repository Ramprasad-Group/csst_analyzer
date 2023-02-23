from enum import Enum
from typing import List, Union

import numpy as np
from pydantic import BaseModel


class PropertyNameEnum(str, Enum):
    TEMP = "temperature"
    TRANS = "transmission"
    BOTTOM_STIR_RATE = "bottom_stir_rate"
    STIR_RATE = "stir_rate"
    CONC = "concentration"
    TIME = "time"
    TEMPERATURE_CHANGE_RATE = "temperature_change_rate"


class PropertyValue(BaseModel):
    """Generic class to hold a single property value

    Args:
        name: Name of the property being stored. Only those in PropertyNameEnum are
            allowed to check for as the package is not designed for other properties.
        unit: Unit of the property (e.g., K (Kelvin), mg/ml, etc...)
        value: Float value of the property
    """
    name: PropertyNameEnum
    unit: str
    value: float

    def __str__(self):
        """String representation is the name, value and unit"""
        return f"{self.name.value} is {self.value} {self.unit}"


class PropertyValues(BaseModel):
    """Generic class to hold a list or 1d numpy array of property values

    Args:
        name: Name of the property being stored. Only those in PropertyNameEnum are
            allowed to check for as the package is not designed for other properties.
        unit: Unit of the property (e.g., K (Kelvin), mg/ml, etc...)
        value: List or 1d numpy array of the property values
    """
    name: PropertyNameEnum
    unit: str
    values: Union[List[float], np.ndarray]

    class Config:
        # added to allow np.ndarray type
        arbitrary_types_allowed = True

    def __str__(self):
        """String representation is just the name (unit) since values would be long"""
        return f"{self.name} ({self.unit})"


class TemperatureSettingEnum(str, Enum):
    HEAT = "heat"
    COOL = "cool"


class TemperatureChange(BaseModel):
    """Temperature change model for temperature program

    Args:
        setting: If the change is to heat or cool.
        to: New temperature value to cool too.
        rate: Rate of change for the temperature value.
    """
    setting: TemperatureSettingEnum
    to: PropertyValue
    rate: PropertyValue


class TemperatureHold(BaseModel):
    """Temperature hold model for temperature program

    Args:
        at: Temperature to hold program at
        for\_: How long to hold the program at the specified temperature
    """
    at: PropertyValue
    for_: PropertyValue


class TemperatureProgram(BaseModel):
    """Temperature program an experiment runs

    Args:
        block: Block samples are loaded in to (e.g., 'A', 'B'...)
        solvent_tune: Tuning process for the solvent prior to loading samples
        sample_load: Temperature samples held at while polymers loaded into the solvent
        experiment: Temperature program for the experiment after tuning and loading
    """

    block: str
    solvent_tune: List[Union[TemperatureChange, TemperatureHold]]
    sample_load: List[Union[TemperatureChange, TemperatureHold]]
    experiment: List[Union[TemperatureChange, TemperatureHold]]


class Reactor(BaseModel):
    """Reactor reading of transmission data

    Each reactor accesses references to shared temperaure, time,
    stir_rate and temperature program data in an experiment.
    Data is shared to avoid duplicating data
    if several reactor access the same temperature, time, etc... data. This data is
    passed to the reactor because it influences the reactor transmission values.

    Indices in the time, transmission, temperature and stir rate lists all match up

    Args:
        solvent: name of the solvent
        polymer: name of the polymer
        conc: concentration of the polymer in the solvent
        temperature_program: Program used to tune and define the crystal 16 run
        transmission: list of transmission values.
        time_since_experiment_start: Time unit and list of values for the experiment.
        actual_temperature: Temperature unit and list of values for the experiment's
            true temperatures
        set_temperature: Temperature unit and list of values for the experiment's
            set temperatures
        stir_rate: Stirring rate unit and list of values for the experiment. Unknown
            why this is different than bottom stir_rate
        bottom_stir_rate: Stiring rate of the bottom stirer
    """

    solvent: str
    polymer: str
    conc: PropertyValue
    # referenced properties
    temperature_program: TemperatureProgram
    transmission: PropertyValues
    actual_temperature: PropertyValues
    set_temperature: PropertyValues
    time_since_experiment_start: PropertyValues
    stir_rates: PropertyValues
    bottom_stir_rate: PropertyValue

    def __str__(self):
        """String representation is the polymer in the solvent at the specific concentration"""
        return f"{self.conc.value} {self.conc.unit} {self.polymer} in {self.solvent}"
