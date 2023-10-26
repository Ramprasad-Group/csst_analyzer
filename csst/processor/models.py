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
    """

    average_temperature: float
    temperature_range: float
    average_transmission: float
    median_transmission: float
    transmission_std: float


class ProcessedReactor(BaseModel):
    """Reactor that has been processed by the processor

    Args:
        unprocessed_reactor: The original, unprocessed reactor. All of its attributes
            are then accessible from the processed reactor.
        temperatures: List of processed temperatures.
    """

    unprocessed_reactor: Reactor
    temperatures: List[ProcessedTemperature]
