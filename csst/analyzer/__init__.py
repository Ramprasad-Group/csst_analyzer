import math
from copy import deepcopy
from datetime import datetime
from typing import List, TextIO

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from csst.analyzer.models import (
    Reactor,
    PropertyValue,
    PropertyValues,
    TemperatureChange,
    TemperatureHold,
    TemperatureProgram,
    AverageTransmission,
    TemperatureSettingEnum
)
from csst.analyzer.helpers import try_parsing_date

__version__ = "0.1.0"

# Colorblind friendly colors
cmap = ["#2D3142", "#E1DAAE", "#058ED9", "#848FA2"]
tempc = "#CC2D35"


class Analyzer:
    """Crystal 16 Dissolition/Solubility Test Analyzer"""
    def __init__(self):
        # initialize necessary attributes
        self.reactors = []

    @classmethod
    def load_from_file(cls, data_path: str) -> 'Analyzer':
        """Load data from a file"""
        # file data
        obj = cls()
        obj.version = None

        # experiment details
        obj.experiment_details = None
        obj.experiment_number = None
        obj.experimenter = None
        obj.project = None
        obj.lab_journal = None
        obj.description = None
        obj.start_of_experiment = None

        # temperature program details
        obj.temperature_program = None
        obj.bottom_stir_rate = None

        # data details
        obj.set_temperature = None
        obj.actual_temperature = None
        obj.time = None
        obj.stir_rate = None

        # Need to find start of data and save header information
        with open(data_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip('\n')
            obj.version = first_line.split(',')[1].split(':')[1].strip()
            if obj.version == '1014':
                obj._load_file_version_1014(f)

        return obj

    def _load_file_version_1014(self, f: TextIO):
        """Loads file version 1014

        Args:
            f: open file to read data from
        """
        # load header data and find where the Temperature Program starts
        # initialize reactor data
        reactors = {}
        for line in f:
            # remove newline characters and csv commas
            line = line.strip("\n")
            line = line.strip(',')
            # found temperature program start
            if "Temperature Program" in line:
                break
            line = line.split(",")
            if line[0] == 'Experiment details':
                if len(line) > 1:
                    self.experiment_details = line[1]
            elif line[0] == 'ExperimentNumber':
                if len(line) > 1:
                    self.experiment_number = line[1]
            elif line[0] == 'Experimentor':
                if len(line) > 1:
                    self.experimenter = line[1]
            elif line[0] == 'Project':
                if len(line) > 1:
                    self.project = line[1]
            elif line[0] == 'Labjournal':
                if len(line) > 1:
                    self.lab_journal = line[1]
            elif line[0] == 'Description':
                if len(line) > 1:
                    self.description = line[1]
            elif line[0] == 'Start of Experiment':
                if len(line) > 1:
                    self.start_of_experiment = try_parsing_date(line[1])
            elif 'Reactor' in line[0]:
                # e.g., Reactor1,5 mg/ml PEG in TOL
                reactor_data = line[1].split()
                # Ignore reactors that are empty
                if float(reactor_data[0]) != 0:
                    reactors[line[0].strip()] = {
                        'conc': PropertyValue(
                            name = 'concentration',
                            value = float(reactor_data[0]),
                            unit = reactor_data[1].strip()
                        ),
                        'polymer': reactor_data[2].strip(),
                        'solvent': reactor_data[4].strip()
                    }

        # Load temperature program
        block = None
        tuning = False
        loading_samples = False
        running_experiment = False
        solvent_tune = []
        sample_load = []
        experiment = []
        for line in f:
            # remove newline characters and csv commas
            line = line.strip("\n")
            line = line.strip(',')
            line = line.split(',')
            # finished reading temperature block
            if "Data Block" in line[0]:
                break
            # switch which part of the temperature program is being read depending on
            # indicators in the file
            if 'Block' in line[0]:
                block = line[1]
                tuning = True
            elif 'Tune' in line[0]:
                tuning = False
                loading_samples = True
            elif 'Stir (Bottom)' in line[0]:
                self.bottom_stir_rate = PropertyValue(
                    name = 'bottom_stir_rate',
                    unit = line[2].strip(),
                    value = float(line[1])
                )
                loading_samples = False
                running_experiment = True
            # Only have experience with bottom stir rate, not sure what to do if the 
            # stir rate is not bottom
            elif 'Stir' in line[0]:
                raise ValueError('Only expected bottom stir rate in temperature program')

            # Load temperature program details
            else:
                step = None
                if 'Heat to' in line[0] or 'Cool to' in line[0]:
                    if 'Heat' in line[0]:
                        setting = TemperatureSettingEnum.HEAT
                    else:
                        setting = TemperatureSettingEnum.COOL
                    rate = line[4].strip()
                    temp_unit = rate.split('/')[0]
                    step = TemperatureChange(
                        setting = setting,
                        to = PropertyValue(
                            name = 'temperature',
                            unit = temp_unit,
                            value = float(line[1])
                        ),
                        rate = PropertyValue(
                            name = 'temperature_change_rate',
                            unit = rate,
                            value = float(line[3])
                        )
                    )
                elif 'Hold at' in line[0]:
                    step = TemperatureHold(
                        at = PropertyValue(
                            name = 'temperature',
                            # a heat to or cool to block will always be before hold at
                            # so the temp unit can be assumed to be the same as the 
                            # prior heat to or cool to
                            unit = temp_unit,
                            value = float(line[1])
                        ),
                        for_ = PropertyValue(
                            name = 'time',
                            unit = line[4].strip(),
                            value = float(line[3])
                        )
                    )
                if step is not None:
                    if tuning:
                        solvent_tune.append(step)
                    elif loading_samples:
                        sample_load.append(step)
                    elif running_experiment:
                        experiment.append(step)

        self.temperature_program = TemperatureProgram(
            block = block,
            solvent_tune = solvent_tune,
            sample_load = sample_load,
            experiment = experiment
        )

        # load data block and get set temperature, actual temperature, time and 
        # stir rates
        df = pd.read_csv(f)
        # get time in hours
        times = df["Decimal Time [mins]"]
        experiment_runtime = []
        for time in times:
            # Account for when day in
            if "." in time:
                t = datetime.strptime(time, "%d.%H:%M:%S")
                val = t.day * 24 + t.hour + t.minute / 60 + t.second / 3600
            else:
                t = datetime.strptime(time, "%H:%M:%S")
                val = t.hour + t.minute / 60 + t.second / 3600
            experiment_runtime.append(val)
        self.experiment_runtime = PropertyValues(
            name = 'time',
            unit = 'hour',
            values = experiment_runtime
        )
        
        set_temp_col = [col for col in df.columns if 'Temperature Setpoint' in col][0]
        self.set_temperature = PropertyValues(
            name = 'temperature',
            unit = set_temp_col.split('[')[1].strip(']').strip(),
            values = df[set_temp_col].to_list()
        )
        actual_temp_col = [col for col in df.columns if 'Temperature Actual' in col][0]
        self.actual_temperature = PropertyValues(
            name = 'temperature',
            unit = actual_temp_col.split('[')[1].strip(']').strip(),
            values = df[actual_temp_col].to_list()
        )
        stir_col = [col for col in df.columns if 'Stirring' in col][0]
        self.stir_rates = PropertyValues(
            name = 'stir_rate',
            unit = stir_col.split('[')[1].strip(']').strip(),
            values = df[stir_col].to_list()
        )

        # configure reactors
        for reactor, parameters in reactors.items():
            reactor_col = [col for col in df.columns if reactor in col][0]
            self.reactors.append(Reactor(
                solvent = parameters['solvent'],
                polymer = parameters['polymer'],
                conc = parameters['conc'],
                transmission = PropertyValues(
                    name = 'transmission',
                    unit = reactor_col.split('[')[1].strip(']').strip(),
                    values = df[reactor_col].to_list()
                ),
                temperature_program = self.temperature_program,
                actual_temperature = self.actual_temperature,
                set_temperature = self.set_temperature,
                experiment_runtime = self.experiment_runtime,
                stir_rates = self.stir_rates,
                bottom_stir_rate = self.bottom_stir_rate
            ))


    def plot_dat(self, figsize=(8, 6)):
        """Plots transmission vs time and temperature"""
        temp_col = ""
        # Temp header has odd symbols that can cause errors, so do this.
        for col in self.df.columns:
            if "Temperature Actual" in col:
                temp_col = col
        temperature = self.df[temp_col]
        transmissions = []
        legend = []
        for sample in self.samples:
            legend.append(self.samples[sample])
            for col in self.df.columns:
                if sample in col:
                    transmissions.append(self.df[col])
        # Convert times from strings to numbers
        times = self.df["Decimal Time [mins]"]

        # Change parameters for plot
        font = {"size": 18}

        matplotlib.rc("font", **font)

        fig = plt.figure(figsize=figsize, tight_layout=True)
        ax1 = fig.add_subplot(111)
        # Make ax2
        ax2 = ax1.twinx()
        ax2.set_ylabel(temp_col.replace("[", "(").replace("]", ")"), color=tempc)
        ax2.tick_params(axis="y", labelcolor=tempc)
        ax2.plot(
            self.df["hours"], temperature, color=tempc, linestyle="dashed", alpha=0.5
        )

        # plot ax1
        ax1.set_xlabel("Time (hours)")
        ax1.set_ylabel("Transmission (%)")

        ax1.set_xlim([0, max(self.df["hours"])])
        ax1.tick_params(axis="y", labelcolor="black")
        curr = 0
        for trans in transmissions:
            ax1.plot(self.df["hours"], trans, color=cmap[curr], linewidth=2.5)
            curr += 1
        fs = 14
        if len(self.samples) > 2:
            offset = -0.425
        else:
            offset = -0.35
        ax1.legend(
            legend,
            bbox_to_anchor=(0, offset, 1, 0.1),
            loc="lower left",
            mode="expand",
            ncol=2,
            fontsize=fs,
        )
        return fig

    def average_transmission_at_temp(
        self, temp: float, temp_range: float = 0
    ) -> List[AverageTransmission]:
        """ "Returns the average transmission at temperature for each reactor

        :parameter temp: Temperature to average at.
        :type temp: float
        :parameter temp_range: When assessing transmissions at this temp,
            look at rows with temp +- (temp_range / 2)
        :type temp_range: float:
        :return: List of AverageTransmission objects
        :rtype: List[AverageTransmission]
        """
        temp_col = [col for col in self.df.columns if "Temperature Actual" in col][0]
        reactor_cols = [
            col
            for col in self.df.columns
            for reactor in self.samples.keys()
            if reactor in col
        ]
        temp_range /= 2
        temp_df = self.df.loc[
            (self.df[temp_col] >= (temp - temp_range))
            & (self.df[temp_col] <= (temp + temp_range))
        ]
        average_transmissions = []
        for reactor_col in reactor_cols:
            sample = [col for col in self.samples.keys() if col in reactor_col][0]
            # In data, most sig figs I've seen is 4, so round to 2 decimal
            # places
            mean = round(temp_df[reactor_col].mean(), 2)
            std = round(temp_df[reactor_col].std(), 2)
            transmissions = temp_df[reactor_col].to_list()
            average_transmissions.append(
                AverageTransmission(
                    reactor=sample,
                    temp=temp,
                    temp_range=temp_range * 2,
                    average_transmission=mean,
                    std=std,
                    transmissions=transmissions,
                )
            )
        return average_transmissions
