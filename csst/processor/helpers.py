from csst.experiment.models import Reactor


def find_index_after_x_hours(
    reactor: Reactor, time_to_skip_in_hours: float = 5 / 60
) -> int:
    """Find first index

    Args:
        reactor: Reactor to find the new start index of.
        time_to_skip_in_hours: time to skip, defaults to 5 minutes

    Returns:
        Index to start at after skipping time
    """
    dt = reactor.experiment.get_timestep_of_experiment()
    # (max of 4 used for test cases)
    return max(int(time_to_skip_in_hours / dt), 4)
