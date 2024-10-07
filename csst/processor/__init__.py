import logging
from typing import Union, List
from math import floor, ceil

import numpy as np

from csst.processor.models import ProcessedTemperature, ProcessedReactor
from csst.processor.helpers import find_index_after_x_hours
from csst.experiment.models import Reactor

logger = logging.getLogger(__name__)


# reactor values sorted by temp would be
# temp = [5, 5, 10, 10, 15, 15, 20, 20, 20, 20]
# trans = [5, 4, 20, 22, 50, 45, 78, 78, 79, 80]
def process_reactor(reactor: Reactor, temp_range=1) -> ProcessedReactor:
    """Process all reactor transmission data

    Find the floor of the min actual temperature and ceil of the max actual temperature,
    then process each integer temperature +/- 0.5.

    Args:
        reactor: reactor to process
    """
    min_temp = floor(min(reactor.experiment.actual_temperature.values))
    max_temp = ceil(max(reactor.experiment.actual_temperature.values))
    temps = np.arange(min_temp, (max_temp + 1), temp_range)
    return ProcessedReactor(
        unprocessed_reactor=reactor,
        temperatures=process_reactor_transmission_at_temps(
            reactor, temps, temp_range=temp_range
        ),
    )


def process_reactor_transmission_at_temps(
    reactor: Reactor,
    temps: List[float],
    temp_range: float = 1,
) -> List[ProcessedTemperature]:
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
            transmissions += ptrans
    return transmissions


def process_reactor_transmission_at_temp(
    reactor: Reactor, temp: float, temp_range: float = 1
) -> Union[None, ProcessedTemperature]:
    """Returns the processed transmission values at the set temperature for the reactor

    Data collected from the temperature program solvent tune and sample load stages
    is skipped, as well as the first two minutes of data collected

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
    # that is the list of indices.
    if temp_range == 0:
        temp_indices = np.where(reactor.experiment.actual_temperature.values == temp)[0]
    else:
        temp_indices = np.where(
            (
                (reactor.experiment.actual_temperature.values < temp + half_range)
                & (reactor.experiment.actual_temperature.values >= temp - half_range)
            )
        )[0]
    start_ind = find_index_after_x_hours(reactor)
    logger.debug(f"Start index for averaging is {start_ind}")
    temp_indices = temp_indices[temp_indices >= start_ind]
    logger.debug(f"temp_indices for temp {temp}: {temp_indices}")
    if len(temp_indices) == 0:
        logger.debug(
            f"No index found at temperature {temp} +/- " + f"{round(temp_range / 2, 2)}"
        )
        return []
    temps = []
    for state in ["heating", "cooling", "holding"]:
        indices = [x for x in temp_indices if reactor.experiment.ramp_state[x] == state]
        if len(indices) == 0:
            continue
        transmission = reactor.transmission.values[indices]
        filtered_transmission = reactor.filtered_transmission.values[indices]
        temps.append(
            ProcessedTemperature(
                average_temperature=temp,
                temperature_range=temp_range,
                average_transmission=transmission.mean(),
                median_transmission=np.median(transmission),
                transmission_std=transmission.std(),
                heating=1 if state == "heating" else 0,
                cooling=1 if state == "cooling" else 0,
                holding=1 if state == "holding" else 0,
                filtered=False,
            )
        )
        temps.append(
            ProcessedTemperature(
                average_temperature=temp,
                temperature_range=temp_range,
                average_transmission=filtered_transmission.mean(),
                median_transmission=np.median(filtered_transmission),
                transmission_std=filtered_transmission.std(),
                heating=1 if state == "heating" else 0,
                cooling=1 if state == "cooling" else 0,
                holding=1 if state == "holding" else 0,
                filtered=True,
            )
        )
    return temps
