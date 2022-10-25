"""Tests csst.csst_analyzer.models.AverageTransmission"""
import pytest

from csst.csst_analyzer.models import AverageTransmission
from .fixtures.data import cssta_obj, fake_cssta_data

def test_average_transmission_get_solubility_based_on_average(fake_cssta_data):
    average_transmissions = fake_cssta_data.average_transmission_at_temp(
            temp=25, temp_range=0)
    for average in average_transmissions:
        if average.reactor == 'Reactor1':
            assert average.get_solubility_based_on_average() == AverageTransmission.PARTIAL