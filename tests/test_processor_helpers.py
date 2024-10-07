from csst.processor import helpers
from .fixtures.data import reactor  # noqa: F401


# Need to figure out what to do about this function
def test_find_index_after_sample_tune_and_load(reactor):  # noqa: F811
    # default minimum
    ind = helpers.find_index_after_x_hours(reactor, time_to_skip_in_hours=0)
    assert ind == 4
    ind = helpers.find_index_after_x_hours(reactor, time_to_skip_in_hours=30 / 60)
    assert ind == 6
