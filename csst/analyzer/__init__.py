import logging

import pandas as pd

from csst.processor import process_reactor
from csst.processor.models import ProcessedTemperature
from csst.experiment.models import Reactor
from csst.experiment import Experiment

logger = logging.getLogger(__name__)

class Analyzer:
    """Crystal 16 Dissolition/Solubility Data Analyzer"""
    def __init__(self):
        self.processed_reactors = []
        columns = ['polymer', 'solvent', 'concentration', 'concentration_unit', 
                    'temperature_unit']
        unproc_columns = ['temperature', 'transmission']
        self.unprocessed_df = pd.DataFrame(columns=columns + unproc_columns)
        proc_columns = list(ProcessedTemperature.__fields__.keys())
        self.df = pd.DataFrame(columns=columns + proc_columns)

    def add_experiment_reactors(self, experiment: Experiment):
        """Adds experiment reactors to Analyzer.reactors list and extends 
        Analyzer.df with the new reactor data
        """
        for reactor in experiment.reactors:
            self.add_reactor(reactor)

    def add_reactor(self, reactor: Reactor):
        """Adds reactor to Analyzer.reactors list and extends 
        Analyzer.df with the new reactor data
        """
        if reactor in [reactor.unprocessed_reactor for reactor in self.processed_reactors]:
            logger.warning(f"Analyzer is not adding the reactor {str(reactor)} because it was previously added")
            return
        reactor = process_reactor(reactor) 
        self.processed_reactors.append(reactor)
        # add processed data
        rows = []
        row = {
            'polymer': reactor.unprocessed_reactor.polymer,
            'solvent': reactor.unprocessed_reactor.solvent,
            'concentration': reactor.unprocessed_reactor.conc.value,
            'concentration_unit': reactor.unprocessed_reactor.conc.unit,
            'temperature_unit': reactor.unprocessed_reactor.actual_temperature.unit,
            'reactor': str(reactor.unprocessed_reactor)
        }
        for temp in reactor.temperatures:
            for field in temp.__fields__:
                row[field] = getattr(temp, field)
            rows.append(row.copy())
        df = pd.DataFrame(rows)
        self.df = pd.concat([self.df, df])

        # add unprocessed data
        rows = []
        row = {
            'polymer': reactor.unprocessed_reactor.polymer,
            'solvent': reactor.unprocessed_reactor.solvent,
            'concentration': reactor.unprocessed_reactor.conc.value,
            'concentration_unit': reactor.unprocessed_reactor.conc.unit,
            'temperature_unit': reactor.unprocessed_reactor.actual_temperature.unit,
            'reactor': str(reactor.unprocessed_reactor)
        }
        for i in range(len(reactor.unprocessed_reactor.actual_temperature.values)):
            row['temperature'] = reactor.unprocessed_reactor.actual_temperature.values[i]
            row['transmission'] = reactor.unprocessed_reactor.transmission.values[i]
            rows.append(row.copy())
        df = pd.DataFrame(rows)
        self.unprocessed_df = pd.concat([self.unprocessed_df, df])
