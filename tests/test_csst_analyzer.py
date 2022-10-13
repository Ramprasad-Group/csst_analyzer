from pathlib import Path

import pytest
import numpy as np

from csst import csst_analyzer
from csst.csst_analyzer import CSSTA
from .fixtures.data import cssta_obj, fake_cssta_data

@pytest.fixture
def csst_expected():
    samples = {
        'Reactor1': '5.11 mg/ml PEG in MeOH',
        'Reactor2': '5.19 mg/ml PEO in MeOH',
        'Reactor3': '5.10 mg/ml PVP in MeOH'
    }
    return samples


def test_CSSTA_init(csst_expected):
    csst_obj = CSSTA(str(Path('test_data') / 'example_data.csv'))
    assert csst_obj.samples == csst_expected

def test_average_transmission_at_temp(fake_cssta_data):
    average_transmissions = fake_cssta_data.average_transmission_at_temp(
            temp=25, temp_range=0)
    # These values because temp_range is 0 and we generated fake data
    # where transmission is a direct function of temperature with no noise.
    for average in average_transmissions:
        if average.reactor == 'Reactor1':
            assert average.transmission == 25
        if average.reactor == 'Reactor2':
            assert average.transmission == 25**2
        if average.reactor == 'Reactor3':
            assert average.transmission == round(np.log(26), 2)

    average_transmissions = fake_cssta_data.average_transmission_at_temp(
            temp=25, temp_range=10)
    for average in average_transmissions:
        # Fake data has real actual temperatures that fluctuate. More than
        # likely, this data is not evenly distributed along the range provided
        # so the std should be smaller than the std of just the range of data
        if average.reactor == 'Reactor1':
            assert average.std <= np.std([20, 30])
        if average.reactor == 'Reactor2':
            assert average.std <= np.std([20**2, 30**2])
        if average.reactor == 'Reactor3':
            assert average.std <= np.std([np.log(20), np.log(30)])
