from enum import Enum
import hashlib
from typing import List, Union, Any, Optional

import numpy as np
from pydantic import BaseModel

from csst.experiment.helpers import json_dumps


class PropertyNameEnum(str, Enum):
    TEMP = "temperature"
    TRANS = "transmission"
    BOTTOM_STIR_RATE = "bottom_stir_rate"
    TOP_STIR_RATE = "top_stir_rate"
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
        return f"{' '.join(self.name.value.capitalize().split('_'))} is {self.value} {self.unit}"


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
        return f"Storing {' '.join(self.name.value.split('_'))} in {self.unit} for {len(self.values)} datapoints"


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

    def __str__(self):
        return f"{self.setting.value.capitalize()} sample {self.to.name} to {self.to.value} {self.to.unit} at rate of {self.rate.value} {self.rate.unit}"


class TemperatureHold(BaseModel):
    """Temperature hold model for temperature program

    Args:
        at: Temperature to hold program at
        for\\_: How long to hold the program at the specified temperature
    """

    at: PropertyValue
    for_: PropertyValue

    def __str__(self) -> str:
        return f"Hold sample at a {self.at.name.value} of {self.at.value} {self.at.unit} for a {self.for_.name.value} of {self.for_.value} {self.for_.unit}"


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

    def hash(self) -> str:
        """Generates deterministic hash in hex format of the temperature program"""
        return hashlib.md5(json_dumps(self.json()).encode("utf-8")).digest().hex()

    def __str__(self) -> str:
        s = f"Block: {self.block}\n\nTuning stage:\n"
        for step in self.solvent_tune:
            s += str(step) + "\n"
        s += "\nSample load stage:\n"
        for step in self.sample_load:
            s += str(step) + "\n"
        s += "\nExperiment stage:\n"
        for step in self.experiment:
            s += str(step) + "\n"
        s = s.strip("\n")
        return s


class FilteredTransmission(BaseModel):
    """Transmissions passed through savgol filter"""

    window_length: int
    polyorder: int
    values: Union[List[float], np.ndarray]

    class Config:
        # added to allow np.ndarray type
        arbitrary_types_allowed = True


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
        solvent_id: id of the solvent in the database, optionally labelled in the
            description. This id is predetermined from the database
        polymer_id: id of the polymer in the database, optionally labelled in the
            description. This id is predetermined from the database
        conc: concentration of the polymer in the solvent
        reactor_number: the reactor number the sample was in
        transmission: list of transmission values.
        filtered_transmission: list of transmissions filtered using savgol_filter
        experiment: experiment the reactor comes from
    """

    solvent: str
    polymer: str
    solvent_id: Optional[int]
    polymer_id: Optional[int]
    conc: PropertyValue
    reactor_number: int
    transmission: PropertyValues
    filtered_transmission: FilteredTransmission
    # referenced properties
    # any type to avoid circular import from importing experiment.
    # This is just supposed to be a reference to the experiment for easier access,
    # so I'm hoping this doesn't cause any issues
    experiment: Any

    def __str__(self):
        """String representation is the polymer in the solvent at the specific concentration"""
        return f"Reactor {self.reactor_number}: {self.conc.value} {self.conc.unit} {self.polymer} in {self.solvent}"
