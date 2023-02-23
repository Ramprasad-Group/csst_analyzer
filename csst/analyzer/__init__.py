import logging

import pandas as pd

from csst.processor import process_reactor
from csst.processor.models import ProcessedTemperature, ProcessedReactor
from csst.experiment.models import Reactor
from csst.experiment import Experiment

logger = logging.getLogger(__name__)


class Analyzer:
    """Crystal 16 Dissolition/Solubility Data Analyzer

    Attributes:
        processed_reactors (List[ProcessedReactor]): List of processed reactors.
        unprocessed_df (pd.DataFrame): Pandas dataframe of all unprocessed reactor data.
            Columns are 'reactor', 'polymer', 'solvent', 
            'concentration', 'concentration_unit', 'set_temperature', 'temperature', 
            'temperature_unit', 'transmission', 'transmission_unit', 'time',
            'time_unit', 'stir_rate', 'stir_rate_unit', 'bottom_stir_rate',
            and 'bottom_stir_rate_unit'
        df (pd.DataFrame): Processed reactor dataframe. Columns are 'reactor', 'polymer',
            'solvent', 'concentration', 'concentration_unit', 'temperature_unit', and
            all attributes in csst.processor.models.ProcessedTemperature.
    """

    def __init__(self):
        self.processed_reactors = []
        columns = [
            "reactor",
            "polymer",
            "solvent",
            "concentration",
            "concentration_unit",
            "temperature_unit",
        ]
        unproc_columns = [
            "temperature", 
            "transmission",
            "set_temperature",
            "time",
            "time_unit",
            "stir_rate",
            "stir_rate_unit",
            "bottom_stir_rate",
            "bottom_stir_rate_unit",
        ]
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
        if reactor in [
            reactor.unprocessed_reactor for reactor in self.processed_reactors
        ]:
            logger.warning(
                f"Analyzer is not adding the reactor {str(reactor)} because it was previously added"
            )
            return
        reactor = process_reactor(reactor)
        self.processed_reactors.append(reactor)
        # add processed data
        rows = []
        row = {
            "polymer": reactor.unprocessed_reactor.polymer,
            "solvent": reactor.unprocessed_reactor.solvent,
            "concentration": reactor.unprocessed_reactor.conc.value,
            "concentration_unit": reactor.unprocessed_reactor.conc.unit,
            "temperature_unit": reactor.unprocessed_reactor.actual_temperature.unit,
            "transmission_unit": reactor.unprocessed_reactor.transmission.unit,
            "reactor": str(reactor.unprocessed_reactor),
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
            "polymer": reactor.unprocessed_reactor.polymer,
            "solvent": reactor.unprocessed_reactor.solvent,
            "concentration": reactor.unprocessed_reactor.conc.value,
            "concentration_unit": reactor.unprocessed_reactor.conc.unit,
            "temperature_unit": reactor.unprocessed_reactor.actual_temperature.unit,
            "time_unit": reactor.unprocessed_reactor.time_since_experiment_start.unit,
            "reactor": str(reactor.unprocessed_reactor),
            "bottom_stir_rate": reactor.unprocessed_reactor.bottom_stir_rate.value,
            "bottom_stir_rate_unit": reactor.unprocessed_reactor.bottom_stir_rate.unit,
            "stir_rate_unit": reactor.unprocessed_reactor.stir_rates.unit,
            "transmission_unit": reactor.unprocessed_reactor.transmission.unit,
        }
        for i in range(len(reactor.unprocessed_reactor.actual_temperature.values)):
            row["temperature"] = reactor.unprocessed_reactor.actual_temperature.values[
                i
            ]
            row["transmission"] = reactor.unprocessed_reactor.transmission.values[i]
            row[
                "time"
            ] = reactor.unprocessed_reactor.time_since_experiment_start.values[i]
            row["set_temperature"] = reactor.unprocessed_reactor.set_temperature.values[
                i
            ]
            row["stir_rate"] = reactor.unprocessed_reactor.stir_rates.values[i]
            rows.append(row.copy())
        df = pd.DataFrame(rows)
        self.unprocessed_df = pd.concat([self.unprocessed_df, df])
