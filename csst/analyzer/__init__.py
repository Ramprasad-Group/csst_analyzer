import logging
from typing import Union, List
import numpy as np

from csst.analyzer.models import ProcessedTransmission
from csst.experiment.models import Reactor

logger = logging.getLogger(__name__)

def process_reactor_transmission_at_temps(
    reactor: Reactor,
    temps: List[float],
    temp_range: float = 0,
) -> List[ProcessedTransmission]:
    """Process the transmission values of the reactor at passed temps.
    
    Args:
        reactor: reactor to process
        temps: temperatures to process
        temp_range: the range of temperatures the transmission is processed from
            (e.g., average_temperature +- (temperature_range / 2)) non-inclusive of
            the upper value.
    """
    transmissions = []
    for temp in temps:
        ptrans = process_reactor_transmission_at_temp(reactor, temp, temp_range)
        if ptrans is not None:
            transmissions.append(ptrans)
    return transmissions


def process_reactor_transmission_at_temp(
    reactor: Reactor,
    temp: float, 
    temp_range: float = 0
) -> Union[None, ProcessedTransmission]:
    """Returns the average transmission at temperature for the reactor

    Args:
        reactor: reactor to process
        temp: temperature to process at
        temp_range: the range of temperatures the transmission is processed from
            (e.g., average_temperature +- (temperature_range / 2)) non-inclusive of
            the upper value.

    Returns:
        Process transmission value or None
    """
    half_range = temp_range / 2
    # where returns a tuple but since this is a 1d array, the tuple has one element
    # that is the list of indices
    if temp_range == 0:
        temp_indices = np.where(
            reactor.actual_temperature.values == temp
        )[0]
    else:
        temp_indices = np.where((
            (reactor.actual_temperature.values < temp + half_range)
          & (reactor.actual_temperature.values >= temp - half_range)
        ))[0]
    if len(temp_indices) == 0:
        logger.debug(f"No index found at temperature {temp} +/- "
            + f"{round(temp_range / 2, 2)}")
        return None
    transmission = reactor.transmission.values[temp_indices]
    return ProcessedTransmission(
        reactor=reactor,
        average_temperature=temp,
        temperature_range=temp_range,
        average=transmission.mean(),
        median=np.median(transmission),
        std=transmission.std()
    )
