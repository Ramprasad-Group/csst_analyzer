import logging
from typing import Dict, List
from pathlib import Path
import glob
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

logger = logging.getLogger(__name__)

class Experiment:
    """Loads Crystal 16 Dissolition/Solubility Test Experiments

    Attributes:
        file_name (str): name of the data file
        version (str): version of the data file
        experiment_details (str):
        experiment_number (str):
        experimenter (str):
        project (str):
        lab_journal (str):
        description (List[str]): Description information with each new line of the
            description appended to a list
        start_of_experiment (datetime.datetime):
            date the experiment started
        polymer_ids (Optioanl[dict]): Optional dictionary with key being polymer name,
            value being polymer id in our database. This is self created and dependent
            on the id in the brettmann polymer database.
        solvent_ids (Optioanl[dict]): Optional dictionary with key being solvent name,
            value being solvent id in our database. This is self created and dependent
            on the id in the brettmann solvent database.
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
        self.file_name = None
        self.version = None
        self.experiment_details = None
        self.experiment_number = None
        self.experimenter = None
        self.project = None
        self.lab_journal = None
        self.description = None
        self.start_of_experiment = None

        # data details
        self.polymer_ids = {}
        self.solvent_ids = {}
        self.temperature_program = None
        self.bottom_stir_rate = None
        self.set_temperature = None
        self.actual_temperature = None
        self.time_since_experiment_start = None
        self.stir_rates = None
        self.reactors = []

    def dict(self) -> Dict[str, str]:
        """Returns dictionary of experiment information, but no reactor,
        temperature program or file_name information
        """
        data = {
            "version": self.version,
            "experiment_details": self.experiment_details,
            "experiment_number": self.experiment_number,
            "experimenter": self.experimenter,
            "project": self.project,
            "lab_journal": self.lab_journal,
            "description": self.description,
            "start_of_experiment": self.start_of_experiment,
        }
        if isinstance(data["description"], list):
            data["description"] = "\n".join(data["description"])
        return data

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
        obj.file_name = Path(data_path).name

        return obj

    def _load_file_version_1014(self, f: TextIO):
        """Loads file version 1014

        Args:
            f: open file to read data from
        """
        # load header data and find where the Temperature Program starts
        # initialize reactor data
        reactors = {}
        description = False
        description_text = []
        for line in f:
            # remove newline characters and csv commas
            line = line.strip("\n")
            line = line.strip(",")
            # found temperature program start
            if "Temperature Program" in line:
                break
            # description saved between description keyword and start of experiment
            # keyword
            elif description and "Start of Experiment" not in line:
                line = line.strip()
                description_text.append(line)
                # e.g., polymer_ids,PEG:34,PEO:46,PVP:41,
                # or solvent_ids,1,2dichlorobenzene:37,Ethyl Acetate:19,MeOH:3,
                if "polymer_ids" in line or "solvent_ids" in line:
                    # pairings = 1,2dichlorobenzene:37,Ethyl Acetate:19,MeOH:3
                    _, pairings = line.split(",", 1)
                    # pairings = ["1,2dichlorobenzene","37,Ethyl Acetate","19,MeOH","3"]
                    pairings = pairings.split(":")
                    # pairings = ["1,2dichlorobenzene","37","Ethyl Acetate","19","MeOH","3"]
                    pairings = (
                        [pairings[0]]
                        + [y for x in pairings[1:-1] for y in x.split(",", maxsplit=1)]
                        + [pairings[-1]]
                    )
                    if "polymer" in line:
                        self.polymer_ids = {
                            pairings[i].strip(): int(pairings[i + 1])
                            for i in range(0, len(pairings), 2)
                        }
                    if "solvent" in line:
                        self.solvent_ids = {
                            pairings[i].strip(): int(pairings[i + 1])
                            for i in range(0, len(pairings), 2)
                        }

            else:
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
                    description = True
                    if len(line) > 1:
                        description_text.append(line[1])
                elif line[0] == "Start of Experiment":
                    description = False
                    self.description = description_text
                    if len(line) > 1:
                        self.start_of_experiment = try_parsing_date(line[1])
                elif "Reactor" in line[0]:
                    # rejoin if there are any commas in polymer or solvent names
                    reactor_data = ",".join(line[1:])
                    # get conc, unit, polymer in solvent
                    conc, unit, pol_sol = reactor_data.split(" ", 2)
                    # e.g., Reactor1,5 mg/ml PEG in TOL
                    # Ignore reactors that are empty
                    if float(conc) != 0:
                        try:
                            pol, sol = pol_sol.split(" in ")
                            reactors[line[0].strip()] = {
                                "conc": PropertyValue(
                                    name="concentration",
                                    value=float(conc),
                                    unit=unit.strip(),
                                ),
                                "polymer": pol.strip(),
                                "solvent": sol.strip(),
                                "reactor_number": int(line[0].strip()[-1]),
                            }
                        except KeyError:
                            logger.info(f"{line} missing polymer or solvent")

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
            solvent_id, polymer_id = None, None
            if parameters["solvent"] in self.solvent_ids:
                solvent_id = self.solvent_ids[parameters["solvent"]]
            if parameters["polymer"] in self.polymer_ids:
                polymer_id = self.polymer_ids[parameters["polymer"]]
            self.reactors.append(
                Reactor(
                    solvent=parameters["solvent"],
                    polymer=parameters["polymer"],
                    solvent_id=solvent_id,
                    polymer_id=polymer_id,
                    conc=parameters["conc"],
                    reactor_number=parameters["reactor_number"],
                    transmission=PropertyValues(
                        name="transmission",
                        unit=reactor_col.split("[")[1].strip("]").strip(),
                        values=df[reactor_col].to_numpy(),
                    ),
                    experiment=self,
                )
            )


def load_experiments_from_folder(
    folder: str, recursive: bool = False
) -> List[Experiment]:
    """Loads all csst experiments in a folder

    Args:
        folder: folder to search experiments for
        recursive: if the folder should be searched recursively. Default False
    Returns:
        List of experiments
    """
    folder = Path(folder)
    if recursive:
        files = list(folder.glob("**/*.csv"))
    else:
        files = list(folder.glob("*.csv"))
    experiments = []
    for file in files:
        logger.info(f"Loading {file}")
        with open(file, "r") as fin:
            if "Crystal16 Data Report File" in fin.readline():
                experiments.append(Experiment.load_from_file(file))
    return experiments
