import pytest
from pathlib import Path

from csst import csst_analyzer
from csst.csst_analyzer import CSSTA

def test_version():
   assert csst_analyzer.__version__ == '0.1.0' 

@pytest.fixture

def test_CSSTA_init():
    Path( 
    CSSTA
