from pathlib import Path

import matplotlib.pyplot as plt
from csst.analyzer import plot
from csst.experiment import Experiment

# Running this script a folder that contains a folder called 'data' with a file in that 
# folder called 'MA-PP-TOL-5-15-30-50 mg.csv'
experiment = Experiment.load_from_file(str(Path('data') / 'MA-PP-TOL-5-15-30-50 mg.csv'))
fig = plot.experiment(experiment)
plt.show()
