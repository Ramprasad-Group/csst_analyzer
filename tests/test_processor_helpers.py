from csst.processor import helpers
from .fixtures.data import reactor  # noqa: F401


def test_find_index_after_sample_tune_and_load(reactor):  # noqa: F811
    ind = helpers.find_index_after_sample_tune_and_load(
        reactor, time_to_skip_in_hours=0
    )
    assert ind == 3
    ind = helpers.find_index_after_sample_tune_and_load(
        reactor, time_to_skip_in_hours=0.2
    )
    assert ind == 5
