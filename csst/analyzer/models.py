from typing import List, ClassVar

from pydantic import BaseModel

class PropertyValue(BaseModel):
    name: str
    unit: str
    value: float

class PropertyValues(BaseModel):
    name: str
    unit: str
    values: List[float]

class TemperatureProgram(BaseModel):
    # TODO Implement once mona describes fully
    deactivated: bool = True

class Reactor(BaseModel):
    """Reactor reading of transmission data

    Each reactor accesses references to shared temperaure, time,
    stir_rate and temperature program data. Data is shared to avoid duplicating data
    if several reactor access the same temperature, time, etc... data. This data is
    passed to the reactor because it influences the reactor transmission values.

    Indices in the time, transmission, temperature and stir rate lists all match up

    Args:
        solvent: name of the solvent
        polymer: name of the polymer
        conc: concentration of the polymer in the solvent
        temperature_program: Program used to tune and define the crystal 16 run
        transmission: list of transmission values.
        time: Time unit and list of values for the experiment. 
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
    time: PropertyValues
    stir_rates: PropertyValues
    bottom_stir_rate: PropertyValue


class AverageTransmission(BaseModel):
    reactor: str
    temp: float
    temp_range: float
    transmissions: List[float]
    average_transmission: float
    std: float

    INSOLUBLE_BELOW_TRANSMISSION: ClassVar[float] = 10
    SOLUBLE_ABOVE_TRANSMISSION: ClassVar[float] = 85
    SOLUBLE: ClassVar[str] = "soluble"
    PARTIAL: ClassVar[str] = "partially_soluble"
    INSOLUBLE: ClassVar[str] = "insoluble"

    def get_solubility_based_on_average(self):
        if self.average_transmission <= self.INSOLUBLE_BELOW_TRANSMISSION:
            return self.INSOLUBLE
        elif self.average_transmission >= self.SOLUBLE_ABOVE_TRANSMISSION:
            return self.SOLUBLE
        else:
            return self.PARTIAL

