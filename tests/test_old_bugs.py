"""This is to test various files that had bugs in them during analysis"""
from pathlib import Path

from csst.experiment import Experiment


def test_invalid_datetime():
    file = Path("test_data") / "old_datetime_format_error.csv"
    exp = Experiment.load_from_file(str(file))
