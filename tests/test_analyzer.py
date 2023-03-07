import pytest

from csst.analyzer import Analyzer

from .fixtures.data import csste_1014, reactor


def test_analyzer_add_reactor(reactor):
    analyzer = Analyzer()
    assert len(analyzer.processed_reactors) == 0
    analyzer.add_reactor(reactor)
    assert len(analyzer.processed_reactors) == 1
    assert list(analyzer.df.polymer.unique()) == ["test_polymer"]
    assert list(analyzer.df.solvent.unique()) == ["test_solvent"]
    assert list(analyzer.df.concentration_unit.unique()) == ["test_concentration"]
    assert analyzer.df.average_transmission.to_list() == [4.5, 21, 47.5, 78.75]
    assert analyzer.df.average_temperature.to_list() == [5, 10, 15, 20]
    temps = analyzer.unprocessed_df.temperature.to_list()
    temps.sort()
    assert temps == [0, 0, 0, 0, 5, 5, 10, 10, 15, 15, 20, 20, 20, 20]
    assert analyzer.unprocessed_df.transmission.to_list() == [
        0,
        0,
        0,
        0,
        5,
        20,
        50,
        78,
        79,
        80,
        78,
        45,
        22,
        4,
    ]
    analyzer.add_reactor(reactor)
    assert len(analyzer.processed_reactors) == 1


def test_analyzer_add_experiment_reactors(csste_1014):
    analyzer = Analyzer()
    assert len(analyzer.processed_reactors) == 0
    analyzer.add_experiment_reactors(csste_1014)
    assert len(analyzer.processed_reactors) == 3
    assert list(analyzer.df.polymer.unique()) == ["PEG", "PEO", "PVP"]
    assert list(analyzer.df.solvent.unique()) == ["MeOH"]
    assert list(analyzer.df.concentration_unit.unique()) == ["mg/ml"]
