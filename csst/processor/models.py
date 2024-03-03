from typing import List
from csst.experiment.models import Reactor

from pydantic import BaseModel


class ProcessedTemperature(BaseModel):
    """model for processed temperature

    Args:
        average_temperature: the average temperature the transmission is processed from
        temperature_range: the range of temperatures the transmission is processed from
            (e.g., average_temperature +- (temperature_range / 2))
        average_transmission: the average transmission
        median_transmission: the median transmission
        transmission_std: standard deviation of the transmissions
        heating: 1 if temperature is being ramped up, else 0
        cooling: 1 id whether temperature is being ramped down, else 0
        holding: 1 if whether temperature is at a hold, else 0
        filtered: True if it has been run through a filter, false otherwise
    """

    average_temperature: float
    temperature_range: float
    average_transmission: float
    median_transmission: float
    transmission_std: float
    heating: int
    cooling: int
    holding: int
    filtered: bool


class ProcessedReactor(BaseModel):
    """Reactor that has been processed by the processor

    Args:
        unprocessed_reactor: The original, unprocessed reactor. All of its attributes
            are then accessible from the processed reactor.
        temperatures: List of processed temperatures.
    """

    unprocessed_reactor: Reactor
    temperatures: List[ProcessedTemperature]
