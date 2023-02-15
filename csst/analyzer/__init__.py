import math
from typing import List, TextIO
from datetime import datetime

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
    TemperatureProgram,
    AverageTransmission
)

__version__ = "0.1.0"

# Colorblind friendly colors
cmap = ["#2D3142", "#E1DAAE", "#058ED9", "#848FA2"]
tempc = "#CC2D35"


class Analyzer:
    """Crystal 16 Dissolition/Solubility Test Analyzer"""
    def __init__(self, data_path: str):
        # initialize necessary attributes
        self.Reactors = []

    def load_from_file(self, data_path: str):
        """Load data from a file"""
        # file data
        self.version = None

        # experiment details
        self.experiment_details = None
        self.experiment_number = None
        self.experimentor = None
        self.project = None
        self.lab_journal = None
        self.description = None
        self.start_of_experiment = None
        self.temperature_program = None

        # data details
        self.set_temperature = None
        self.actual_temperature = None
        self.time = None
        self.stir_rate = None

        # Need to find start of data and save header information
        with open(data_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip('\n')
            self.version = first_line.split(',')[1].split(':')[1].strip()
            if self.version == '1014':
                self._load_file_version_1014(f)

    def _load_file_version_1014(self, f: TextIO):
        """Loads file version 1014

        Args:
            f: open file to read data from
        """
        data_line_start = 1
        # load header data and find where the Temperature Program starts
        # initialize reactor data
        reactors = []
        for line in f:
            # remove newline characters and csv commas
            line = line.strip("\n")
            line = line.strip(',')
            data_start += 1
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
                    self.experimentor = line[1]
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
                    # e.g., 2/24/2022  2:22:00 PM
                    self.start_of_experiment = datetime.strptime(
                        line[1], 
                        '%m/%d/%Y %H:%M:%S %p'
                    ) 
            elif 'Reactor' in line[0]:
                # e.g., Reactor1,5 mg/ml PEG in TOL
                reactor_data = line[1].split()
                reactors.append({
                    'conc': reactor_data[0],
                    'conc_unit': reactor_data[1],
                    'polymer': reactor_data[2],
                    'solvent': reactor_data[4]
                }


        self.df = pd.read_csv(data_path, header=data_start)
        times = self.df["Decimal Time [mins]"]
        num_times = []
        for time in times:
            # Account for when day in
            if "." in time:
                t = datetime.strptime(time, "%d.%H:%M:%S")
                val = t.day * 24 + t.hour + t.minute / 60 + t.second / 3600
            else:
                t = datetime.strptime(time, "%H:%M:%S")
                val = t.hour + t.minute / 60 + t.second / 3600
            num_times.append(val)
        self.df["hours"] = num_times

        self.header_data = header_data

        # Find samples
        samples = {}
        for key in header_data:
            if "Reactor" in key:
                val = header_data[key][0]
                val.split(" ")
                if int(val[0]) != 0:
                    samples[key] = header_data[key][0]
        self.samples = samples

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
