import pytest

from csst.csst_analyzer import data_analysis 
from csst.csst_analyzer.data_analysis import divisions

def test_multiply_by_2():
    assert data_analysis.multiply_by_two(2) == 4

def test_divided_by_2():
    assert divisions.divide_by_2(8) == 4
