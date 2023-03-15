import pytest
from datetime import datetime

from csst.experiment.helpers import (
    try_parsing_date,
    json_dumps,
    remove_keys_with_null_values_in_dict,
)


def test_try_parsing_dates():
    dates = {
        "8/19/22 13:54": datetime(year=2022, month=8, day=19, hour=13, minute=54),
        "2/24/2022  2:22:00 PM": datetime(
            year=2022, month=2, day=24, hour=14, minute=22, second=0
        ),
        "2/24/2022  2:22:00 AM": datetime(
            year=2022, month=2, day=24, hour=2, minute=22, second=0
        ),
        "2/10/2022  1:14:00 PM": datetime(
            year=2022, month=2, day=10, hour=13, minute=14, second=0
        ),
    }
    for date, expected_datetime in dates.items():
        assert try_parsing_date(date) == expected_datetime

    with pytest.raises(ValueError):
        try_parsing_date("January 6 2022")


def test_json_dumps():
    data = {"test": "data", "atest2": "data"}
    dump = json_dumps(data)
    assert isinstance(dump, str)
    assert dump == '{"atest2":"data","test":"data"}'


def test_remove_keys_with_null_values_in_dict():
    data = {"test": None, "test2": 2, "test3": None, "test5": 6}
    clean_data = remove_keys_with_null_values_in_dict(data)
    assert "test" not in clean_data
    assert "test3" not in clean_data
    assert data["test2"] == clean_data["test2"]
    assert data["test5"] == clean_data["test5"]
