from bisect import bisect_right

from csst.experiment.models import Reactor, TemperatureHold


def find_index_after_sample_tune_and_load(
    reactor: Reactor, time_to_skip_in_hours: float = 2 / 60
) -> int:
    """Find first reactor index after skipping the tuning and sample loading stages

    Args:
        reactor: Reactor to find the new start index of.
        time_to_skip_in_hours: Additional time to skip that will be added to the
            tuning and loading stage time. Default is 2 additional minutes.

    Returns:
        Index to start at after skipping tune and load
    """
    for stage in [
        reactor.experiment.temperature_program.solvent_tune,
        reactor.experiment.temperature_program.sample_load,
    ]:
        for step in stage:
            if isinstance(step, TemperatureHold):
                if step.for_.unit == "sec":
                    time_to_skip_in_hours += step.for_.value / 3600
                else:
                    raise NotImplementedError(
                        "Conversion of tuning and sample load "
                        + "hold times is only implemented from 'sec' to hour."
                    )
    # find new start if the time is skipped
    return bisect_right(
        reactor.experiment.time_since_experiment_start.values, time_to_skip_in_hours
    )
