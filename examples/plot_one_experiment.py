from pathlib import Path

import matplotlib.pyplot as plt
from csst.experiment import Experiment
from csst.analyzer.plotter import plot_experiment

# Running this script a folder that contains a folder called 'data' with a file in that
# folder called 'MA-PP-TOL-5-15-30-50 mg.csv'
experiment = Experiment.load_from_file(
    str(Path("data") / "MA-PP-TOL-5-15-30-50 mg.csv")
)
fig = plot_experiment(experiment)
plt.show()
