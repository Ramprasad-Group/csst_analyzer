from pathlib import Path

import pytest
import numpy as np

from csst import analyzer
from csst.analyzer import Analyzer
from .fixtures.data import cssta_1014, test_cssta, manual_1014

def test_analyzer_init_from_file_version_1014(cssta_1014, manual_1014):
    # test headers
    assert cssta_1014.experiment_details == manual_1014.experiment_details
    assert cssta_1014.experiment_number == manual_1014.experiment_number
    assert cssta_1014.experimenter == manual_1014.experimenter
    assert cssta_1014.project == manual_1014.project
    assert cssta_1014.lab_journal == manual_1014.lab_journal
    assert cssta_1014.description == manual_1014.description
    assert cssta_1014.start_of_experiment == manual_1014.start_of_experiment

    assert cssta_1014.temperature_program.block == manual_1014.temperature_program.block
    assert cssta_1014.bottom_stir_rate == manual_1014.bottom_stir_rate
    assert len(manual_1014.temperature_program.solvent_tune) == len(cssta_1014.temperature_program.solvent_tune)
    for i in range(len(cssta_1014.temperature_program.solvent_tune)):
        assert manual_1014.temperature_program.solvent_tune[i] == cssta_1014.temperature_program.solvent_tune[i]

    assert len(manual_1014.temperature_program.sample_load) == len(cssta_1014.temperature_program.sample_load)
    for i in range(len(cssta_1014.temperature_program.sample_load)):
        assert manual_1014.temperature_program.sample_load[i] == cssta_1014.temperature_program.sample_load[i]

    assert len(manual_1014.temperature_program.experiment) == len(cssta_1014.temperature_program.experiment)
    for i in range(len(cssta_1014.temperature_program.experiment)):
        assert manual_1014.temperature_program.experiment[i] == cssta_1014.temperature_program.experiment[i]

    assert manual_1014.temperature_program == cssta_1014.temperature_program




def test_average_transmission_at_temp(test_cssta):
    average_transmissions = test_cssta.average_transmission_at_temp(
        temp=25, temp_range=0
    )
    # These values because temp_range is 0 and we generated fake data
    # where transmission is a direct function of temperature with no noise.
    for average in average_transmissions:
        if average.reactor == "Reactor1":
            assert average.average_transmission == 25
            for transmission in average.transmissions:
                assert transmission == 25
        if average.reactor == "Reactor2":
            assert average.average_transmission == 25**2
            for transmission in average.transmissions:
                assert transmission == 25**2
        if average.reactor == "Reactor3":
            assert average.average_transmission == round(np.log(26), 2)
            for transmission in average.transmissions:
                assert round(transmission, 2) == round(np.log(26), 2)

    average_transmissions = test_cssta.average_transmission_at_temp(
        temp=25, temp_range=10
    )
    for average in average_transmissions:
        # Fake data has real actual temperatures that fluctuate. More than
        # likely, this data is not evenly distributed along the range provided
        # so the std should be smaller than the std of just the range of data
        if average.reactor == "Reactor1":
            assert average.std <= np.std([20, 30])
            for transmission in average.transmissions:
                assert transmission >= 20 or transmission <= 30
        if average.reactor == "Reactor2":
            assert average.std <= np.std([20**2, 30**2])
            for transmission in average.transmissions:
                assert transmission >= 20**2 or transmission <= 30**2
        if average.reactor == "Reactor3":
            assert average.std <= np.std([np.log(20), np.log(30)])
            for transmission in average.transmissions:
                assert transmission >= np.log(20) or transmission <= np.log(30)
