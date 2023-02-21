import pytest

from csst.processor import (
    process_reactor_transmission_at_temp,
    process_reactor_transmission_at_temps,
    process_reactor
)
from csst.experiment.models import PropertyValues, PropertyValue
from .fixtures.data import reactor


def test_process_reactor_transmission_at_temp(reactor):
    """Tests processing of transmission. See reactor fixture for data"""
    ptrans = process_reactor_transmission_at_temp(reactor, temp=5)
    assert ptrans.average_transmission == 4.5
    assert ptrans.median_transmission == 4.5
    assert round(ptrans.transmission_std, 3) == 0.5

    ptrans = process_reactor_transmission_at_temp(reactor, temp=5, temp_range=10)
    assert ptrans.average_transmission == 4.5
    assert ptrans.median_transmission == 4.5
    assert round(ptrans.transmission_std, 3) == 0.5

    ptrans = process_reactor_transmission_at_temp(reactor, temp=5, temp_range=11)
    assert ptrans.average_transmission == 12.75
    assert ptrans.median_transmission == 12.5
    assert round(ptrans.transmission_std, 3) == 8.288

    ptrans = process_reactor_transmission_at_temp(reactor, temp=15, temp_range=11)
    assert ptrans.average_transmission == 56.5
    assert ptrans.median_transmission == 64
    assert round(ptrans.transmission_std, 3) == 24.187

    assert process_reactor_transmission_at_temp(reactor, temp=0) is None


def test_process_reactor_transmission_at_temps(reactor):
    ptransmissions = process_reactor_transmission_at_temps(reactor, [5, 10, 15, 20])
    averages = [ptrans.average_transmission for ptrans in ptransmissions]
    temps = [ptrans.average_temperature for ptrans in ptransmissions]
    averages.sort()
    expected_averages = [4.5, 21, 47.5, 78.75]
    assert averages == expected_averages
    assert temps == [5, 10, 15, 20]

    ptransmissions = process_reactor_transmission_at_temps(
        reactor, [6, 11, 16, 19, 21], 2
    )
    averages = [ptrans.average_transmission for ptrans in ptransmissions]
    temps = [ptrans.average_temperature for ptrans in ptransmissions]
    averages.sort()
    expected_averages = [4.5, 21, 47.5, 78.75]
    assert averages == expected_averages
    assert temps == [6, 11, 16, 21]

def test_process_ractor_data(reactor):
    preactor = process_reactor(reactor)
    assert preactor.unprocessed_reactor == reactor
    expected_averages = [4.5, 21, 47.5, 78.75]
    averages = [ptemp.average_transmission for ptemp in preactor.temperatures]
    temps = [ptemp.average_temperature for ptemp in preactor.temperatures]
    assert averages == expected_averages
    assert temps == [5, 10, 15, 20]
    
