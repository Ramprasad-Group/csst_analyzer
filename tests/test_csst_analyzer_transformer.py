import pytest
import numpy as np
import pandas as pd

from csst.csst_analyzer import transformer

@pytest.fixture
def data():
    x = list(range(0,100))
    y = [np.sin(i) for i in x]
    df = pd.DataFrame({'x': x, 'y': y})
    return 'x', 'y', df

def test_average_data_transformer(data):
    x_col, y_col, df = data
    transformed_data = transformer.average_data_transformer(df, x_col, y_col)
    assert transformed_data is None
    
