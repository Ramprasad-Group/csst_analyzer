from pathlib import Path

import pandas as pd
import numpy as np
import pytest

from csst.csst_analyzer import CSSTA

@pytest.fixture
def cssta_obj():
    cssta_obj = CSSTA(str(Path(__file__ ).parent.absolute() / '..' / 
                          'test_data' / 'example_data.csv'))
    return cssta_obj

@pytest.fixture
def fake_cssta_data(cssta_obj):
    """Convert cssta_obj dataframe reactor data

    Reactor1 data will be simple be the actual temp

    Reactor2 data will be the actual temp squared

    Reactor3 data will be the log of the absolute value of the actual temp + 1
    """
    temp_col = [col for col in cssta_obj.df.columns 
                if 'Temperature Actual' in col][0]
    reactor_cols = [col for col in cssta_obj.df.columns for reactor in 
                    cssta_obj.samples.keys() if reactor in col]
    for col in reactor_cols:
        if 'Reactor1' in col:
            fake_data = cssta_obj.df[temp_col].to_list()
            cssta_obj.df[col] = fake_data.copy()
        if 'Reactor2' in col:
            fake_data = [t**2 for t in cssta_obj.df[temp_col].to_list()]
            cssta_obj.df[col] = fake_data.copy()
        if 'Reactor3' in col:
            fake_data = [np.log(abs(t) + 1) 
                         for t in cssta_obj.df[temp_col].to_list()]
            cssta_obj.df[col] = fake_data.copy()
    return cssta_obj
