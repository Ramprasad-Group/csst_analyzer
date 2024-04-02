from bisect import bisect_right

from csst.experiment.models import Reactor, TemperatureHold


def find_index_after_sample_tune_and_load(
    reactor: Reactor, time_to_skip_in_hours: float = 2 / 60
) -> int:
    """Find first reactor index after skipping the tuning and sample loading stages

    Sometimes there is not tuning phase, so I need to rework how this function
    operates. In the mean time, I will just assum the first five minutes of the test
    are invalid.

    Args:
        reactor: Reactor to find the new start index of.
        time_to_skip_in_hours: Additional time to skip that will be added to the
            tuning and loading stage time. Default is 2 additional minutes.

    Returns:
        Index to start at after skipping tune and load
    """
    # This function works, just tuning phase isn't always valid
    #     for stage in [
    #         reactor.experiment.temperature_program.solvent_tune,
    #         reactor.experiment.temperature_program.sample_load,
    #     ]:
    #         for step in stage:
    #             if isinstance(step, TemperatureHold):
    #                 if step.for_.unit == "sec":
    #                     time_to_skip_in_hours += step.for_.value / 3600
    #                 else:
    #                     raise NotImplementedError(
    #                         "Conversion of tuning and sample load "
    #                         + "hold times is only implemented from 'sec' to hour."
    #                     )
    #     # find new start if the time is skipped
    #     return bisect_right(
    #         reactor.experiment.time_since_experiment_start.values, time_to_skip_in_hours
    #     )
    dt = reactor.experiment.get_timestep_of_experiment()
    # five minutes of data
    return max(int((5 * 60 / 3600) / dt), 5)
