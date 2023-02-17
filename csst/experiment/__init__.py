from datetime import datetime
from typing import TextIO

import pandas as pd
from csst.experiment.helpers import try_parsing_date
from csst.experiment.models import (
    Reactor,
    PropertyValue,
    PropertyValues,
    TemperatureChange,
    TemperatureHold,
    TemperatureProgram,
    TemperatureSettingEnum,
)


class Experiment:
    """Loads Crystal 16 Dissolition/Solubility Test Experiments

    Attributes:
        version: version of the data file
        experiment_details (str):
        experiment_number (str):
        project (str):
        lab_journal (str):
        description (str):
        start_of_experiment (datetime.datetime):
            date the experiment started
        temperature_program (TemperatureProgram):
            Program used to tune solvent, load polymers and change the
            experiment temperature conditions.
        bottom_stir_rate (PropertyValue):
            Rate spinner is spinning at the bottom of the sample during the course
            of the experiment.
        set_temperature (PropertyValues):
            List of set temperatures the experiment is supposed to be at during each
            time step.
        actual_temperature (PropertyValues):
            List of actual temperature the experiment is at during each time step.
        time_since_experiment_start (PropertyValues):
            List of times corresponding to when the experiment was started. Indices
            match actual/set temperatures, stir_rates and reactor transmissions indices.
        stir_rates (PropertyValues):
            Unknown stir rates measured by machine. Typically 0 and separate from the
            bottom stir rate.
        reactors (List[Reactor]):
            List of reactors. Each reactor keeps track of the polymer, solvent,
            concentration and tranmission percentage (see Reactor documentation).
    """

    def __init__(self):
        """Initialize attirbutes"""
        # experiment details
        self.version = None
        self.experiment_details = None
        self.experiment_number = None
        self.experimenter = None
        self.project = None
        self.lab_journal = None
        self.description = None
        self.start_of_experiment = None
        self.temperature_program = None

        # data details
        self.bottom_stir_rate = None
        self.set_temperature = None
        self.actual_temperature = None
        self.time_since_experiment_start = None
        self.stir_rates = None
        self.reactors = []

    @classmethod
    def load_from_file(cls, data_path: str) -> "Experiment":
        """Load data from a file"""
        obj = cls()
        # Need to find start of data and save header information
        with open(data_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip("\n")
            obj.version = first_line.split(",")[1].split(":")[1].strip()
            if obj.version == "1014":
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
            line = line.strip(",")
            # found temperature program start
            if "Temperature Program" in line:
                break
            line = line.split(",")
            if line[0] == "Experiment details":
                if len(line) > 1:
                    self.experiment_details = line[1]
            elif line[0] == "ExperimentNumber":
                if len(line) > 1:
                    self.experiment_number = line[1]
            elif line[0] == "Experimentor":
                if len(line) > 1:
                    self.experimenter = line[1]
            elif line[0] == "Project":
                if len(line) > 1:
                    self.project = line[1]
            elif line[0] == "Labjournal":
                if len(line) > 1:
                    self.lab_journal = line[1]
            elif line[0] == "Description":
                if len(line) > 1:
                    self.description = line[1]
            elif line[0] == "Start of Experiment":
                if len(line) > 1:
                    self.start_of_experiment = try_parsing_date(line[1])
            elif "Reactor" in line[0]:
                # e.g., Reactor1,5 mg/ml PEG in TOL
                reactor_data = line[1].split()
                # Ignore reactors that are empty
                if float(reactor_data[0]) != 0:
                    reactors[line[0].strip()] = {
                        "conc": PropertyValue(
                            name="concentration",
                            value=float(reactor_data[0]),
                            unit=reactor_data[1].strip(),
                        ),
                        "polymer": reactor_data[2].strip(),
                        "solvent": reactor_data[4].strip(),
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
            line = line.strip(",")
            line = line.split(",")
            # finished reading temperature block
            if "Data Block" in line[0]:
                break
            # switch which part of the temperature program is being read depending on
            # indicators in the file
            if "Block" in line[0]:
                block = line[1]
                tuning = True
            elif "Tune" in line[0]:
                tuning = False
                loading_samples = True
            elif "Stir (Bottom)" in line[0]:
                self.bottom_stir_rate = PropertyValue(
                    name="bottom_stir_rate", unit=line[2].strip(), value=float(line[1])
                )
                loading_samples = False
                running_experiment = True
            # Only have experience with bottom stir rate, not sure what to do if the
            # stir rate is not bottom
            elif "Stir" in line[0]:
                raise ValueError(
                    "Only expected bottom stir rate in temperature program"
                )

            # Load temperature program details
            else:
                step = None
                if "Heat to" in line[0] or "Cool to" in line[0]:
                    if "Heat" in line[0]:
                        setting = TemperatureSettingEnum.HEAT
                    else:
                        setting = TemperatureSettingEnum.COOL
                    rate = line[4].strip()
                    temp_unit = rate.split("/")[0]
                    step = TemperatureChange(
                        setting=setting,
                        to=PropertyValue(
                            name="temperature", unit=temp_unit, value=float(line[1])
                        ),
                        rate=PropertyValue(
                            name="temperature_change_rate",
                            unit=rate,
                            value=float(line[3]),
                        ),
                    )
                elif "Hold at" in line[0]:
                    step = TemperatureHold(
                        at=PropertyValue(
                            name="temperature",
                            # a heat to or cool to block will always be before hold at
                            # so the temp unit can be assumed to be the same as the
                            # prior heat to or cool to
                            unit=temp_unit,
                            value=float(line[1]),
                        ),
                        for_=PropertyValue(
                            name="time", unit=line[4].strip(), value=float(line[3])
                        ),
                    )
                if step is not None:
                    if tuning:
                        solvent_tune.append(step)
                    elif loading_samples:
                        sample_load.append(step)
                    elif running_experiment:
                        experiment.append(step)

        self.temperature_program = TemperatureProgram(
            block=block,
            solvent_tune=solvent_tune,
            sample_load=sample_load,
            experiment=experiment,
        )

        # load data block and get set temperature, actual temperature, time and
        # stir rates
        df = pd.read_csv(f)
        # get time in hours
        times = df["Decimal Time [mins]"]
        time_since_experiment_start = []
        for time in times:
            # Account for when day in
            if "." in time:
                t = datetime.strptime(time, "%d.%H:%M:%S")
                val = t.day * 24 + t.hour + t.minute / 60 + t.second / 3600
            else:
                t = datetime.strptime(time, "%H:%M:%S")
                val = t.hour + t.minute / 60 + t.second / 3600
            time_since_experiment_start.append(val)
        self.time_since_experiment_start = PropertyValues(
            name="time", unit="hour", values=time_since_experiment_start
        )

        set_temp_col = [col for col in df.columns if "Temperature Setpoint" in col][0]
        self.set_temperature = PropertyValues(
            name="temperature",
            unit=set_temp_col.split("[")[1].strip("]").strip(),
            values=df[set_temp_col].to_numpy(),
        )
        actual_temp_col = [col for col in df.columns if "Temperature Actual" in col][0]
        self.actual_temperature = PropertyValues(
            name="temperature",
            unit=actual_temp_col.split("[")[1].strip("]").strip(),
            values=df[actual_temp_col].to_numpy(),
        )
        stir_col = [col for col in df.columns if "Stirring" in col][0]
        self.stir_rates = PropertyValues(
            name="stir_rate",
            unit=stir_col.split("[")[1].strip("]").strip(),
            values=df[stir_col].to_numpy(),
        )

        # configure reactors
        for reactor, parameters in reactors.items():
            reactor_col = [col for col in df.columns if reactor in col][0]
            self.reactors.append(
                Reactor(
                    solvent=parameters["solvent"],
                    polymer=parameters["polymer"],
                    conc=parameters["conc"],
                    transmission=PropertyValues(
                        name="transmission",
                        unit=reactor_col.split("[")[1].strip("]").strip(),
                        values=df[reactor_col].to_numpy(),
                    ),
                    temperature_program=self.temperature_program,
                    actual_temperature=self.actual_temperature,
                    set_temperature=self.set_temperature,
                    time_since_experiment_start=self.time_since_experiment_start,
                    stir_rates=self.stir_rates,
                    bottom_stir_rate=self.bottom_stir_rate,
                )
            )
