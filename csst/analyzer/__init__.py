import math
from typing import List
from datetime import datetime

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from csst.analyzer.models import AverageTransmission

__version__ = "0.1.0"

# Colorblind friendly colors
cmap = ['#2D3142', '#E1DAAE', '#058ED9', '#848FA2']
tempc = '#CC2D35'

class CSSTA:
    """Crystal 16 Dissolition/Solubility Test Analyzer (CSSTA)
    
    Analyzes CSST data and returns generated plots and analysis
    """
    def __init__(self, data_path):
        """Initialize analyzer by importing data

        :parameter data_path: File location of csv data on computer
        :type data_path: str
        """
        # Need to find start of data and save header information
        f = open(data_path, "r", encoding='utf-8')
        data_start = 0
        header_data = {}
        Lines = f.readlines()
        for line in Lines:
            # Pandas clears out blank spaces, so we can ignore those when
            # counting the start location of the data
            line = line.replace('\n','')
            if len(line) == 0:
                continue
            data_start += 1
            if 'Data Block' in line:
                break
            else:
                line = line.split(',')
                if len(line) > 1:
                    key = line[0]
                    val = line[1:] 
                    header_data[key] = val
        f.close()
        self.df = pd.read_csv(data_path, header=data_start)
        times = self.df['Decimal Time [mins]']
        num_times = []
        for time in times:
            # Account for when day in 
            if '.' in time:
                t = datetime.strptime(time,"%d.%H:%M:%S")
                val = t.day*24 + t.hour + t.minute/60 + t.second/3600
            else:
                t = datetime.strptime(time,"%H:%M:%S")
                val = t.hour + t.minute/60 + t.second/3600
            num_times.append(val)
        self.df['hours'] = num_times
        
        self.header_data = header_data
        
        # Find samples
        samples = {}
        for key in header_data:
            if 'Reactor' in key:
                val = header_data[key][0]
                val.split(' ')
                if (int(val[0]) != 0):
                    samples[key] = header_data[key][0]
        self.samples = samples

    def plot_dat(self, figsize=(8,6)):
        """Plots transmission vs time and temperature"""
        temp_col = ''
        # Temp header has odd symbols that can cause errors, so do this.
        for col in self.df.columns:
            if 'Temperature Actual' in col:
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
        times = self.df['Decimal Time [mins]']

        # Change parameters for plot
        font = {'size'   : 18}

        matplotlib.rc('font', **font)

        fig = plt.figure(figsize=figsize, tight_layout=True)
        ax1 = fig.add_subplot(111)
        # Make ax2
        ax2 = ax1.twinx()
        ax2.set_ylabel(temp_col.replace('[','(').replace(']',')'), 
                       color=tempc)
        ax2.tick_params(axis='y', labelcolor=tempc)
        ax2.plot(self.df['hours'], temperature, color=tempc, linestyle='dashed',
                alpha=.5)

        # plot ax1
        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('Transmission (%)')

        ax1.set_xlim([0, max(self.df['hours'])])
        ax1.tick_params(axis='y', labelcolor='black')
        curr = 0
        for trans in transmissions:
            ax1.plot(self.df['hours'], trans, color=cmap[curr], linewidth=2.5)
            curr += 1
        fs = 14
        if len(self.samples) > 2:
            offset = -0.425
        else:
            offset = -0.35
        ax1.legend(legend, bbox_to_anchor=(0,offset,1,0.1), loc="lower left",
                   mode="expand", ncol=2, fontsize=fs)
        return fig

    def average_transmission_at_temp(self, temp: float, 
                temp_range: float = 0) -> List[AverageTransmission]:
        """"Returns the average transmission at temperature for each reactor 

        :parameter temp: Temperature to average at.
        :type temp: float
        :parameter temp_range: When assessing transmissions at this temp,
            look at rows with temp +- (temp_range / 2)
        :type temp_range: float:
        :return: List of AverageTransmission objects
        :rtype: List[AverageTransmission]
        """
        temp_col = [col for col in self.df.columns 
                    if 'Temperature Actual' in col][0]
        reactor_cols = [col for col in self.df.columns for reactor in 
                        self.samples.keys() if reactor in col]
        temp_range /= 2
        temp_df = self.df.loc[(self.df[temp_col] >= (temp - temp_range))
                            & (self.df[temp_col] <= (temp + temp_range))]
        average_transmissions = []
        for reactor_col in reactor_cols:
            sample = [col for col in self.samples.keys() if col in 
                      reactor_col][0]
            # In data, most sig figs I've seen is 4, so round to 2 decimal
            # places
            mean = round(temp_df[reactor_col].mean(), 2)
            std = round(temp_df[reactor_col].std(), 2)
            transmissions = temp_df[reactor_col].to_list()
            average_transmissions.append(AverageTransmission(reactor=sample,
                    temp=temp, temp_range=temp_range*2,
                    average_transmission=mean, std=std, 
                    transmissions=transmissions))
        return average_transmissions
