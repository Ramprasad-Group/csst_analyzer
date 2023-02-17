"""Tests csst.analyzer.models.AverageTransmission"""
import pytest

from csst.analyzer import (
    process_reactor_transmission_at_temp,
    process_reactor_transmission_at_temps,
)
from csst.experiment.models import PropertyValues, PropertyValue
from .fixtures.data import reactor


def test_process_reactor_transmission_at_temp(reactor):
    """Tests processing of transmission. See reactor fixture for data"""
    ptrans = process_reactor_transmission_at_temp(reactor, temp=5)
    assert ptrans.average == 4.5
    assert ptrans.median == 4.5
    assert ptrans.reactor == reactor
    assert round(ptrans.std, 3) == 0.5

    ptrans = process_reactor_transmission_at_temp(reactor, temp=5, temp_range=10)
    assert ptrans.average == 4.5
    assert ptrans.median == 4.5
    assert ptrans.reactor == reactor
    assert round(ptrans.std, 3) == 0.5

    ptrans = process_reactor_transmission_at_temp(reactor, temp=5, temp_range=11)
    assert ptrans.average == 12.75
    assert ptrans.median == 12.5
    assert ptrans.reactor == reactor
    assert round(ptrans.std, 3) == 8.288

    ptrans = process_reactor_transmission_at_temp(reactor, temp=15, temp_range=11)
    assert ptrans.average == 56.5
    assert ptrans.median == 64
    assert ptrans.reactor == reactor
    assert round(ptrans.std, 3) == 24.187

    assert process_reactor_transmission_at_temp(reactor, temp=0) is None


def test_process_reactor_transmission_at_temps(reactor):
    # reactor values sorted by temp would be
    # temp = [5, 5, 10, 10, 15, 15, 20, 20, 20, 20]
    # trans = [5, 4, 20, 22, 50, 45, 78, 78, 79, 80]
    ptransmissions = process_reactor_transmission_at_temps(reactor, [5, 10, 15, 20])
    averages = [ptrans.average for ptrans in ptransmissions]
    temps = [ptrans.average_temperature for ptrans in ptransmissions]
    averages.sort()
    expected_averages = [4.5, 21, 47.5, 78.75]
    assert averages == expected_averages
    assert temps == [5, 10, 15, 20]

    ptransmissions = process_reactor_transmission_at_temps(
        reactor, [6, 11, 16, 19, 21], 2
    )
    averages = [ptrans.average for ptrans in ptransmissions]
    temps = [ptrans.average_temperature for ptrans in ptransmissions]
    averages.sort()
    expected_averages = [4.5, 21, 47.5, 78.75]
    assert averages == expected_averages
    assert temps == [6, 11, 16, 21]
