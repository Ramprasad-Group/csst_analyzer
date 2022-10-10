import pytest
from pathlib import Path

from csst import csst_analyzer
from csst.csst_analyzer import CSSTA

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
