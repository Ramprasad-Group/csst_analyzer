from enum import Enum
from typing import List, ClassVar

from csst.experiment.models import Reactor

from pydantic import BaseModel


class SolubilityEnum(Enum):
    SOLUBLE = "soluble"
    INSOLUBLE = "insoluble"
    PARTIAL = "partially_soluble"


class ProcessedTransmission(BaseModel):
    """model for processed transmission data

    Args:
        reactor: Reactor the data is processed from
        average_temperature: the average temperature the transmission is processed from
        temperature_range: the range of temperatures the transmission is processed from
            (e.g., average_temperature +- (temperature_range / 2))
        average: the average transmission
        median: the median transmission
        std: standard deviation of the transmissions
    """

    reactor: Reactor
    average_temperature: float
    temperature_range: float
    average: float
    median: float
    std: float
