from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from csst.experiment import Experiment
from csst.analyzer import Analyzer

# Running this script a folder that contains a folder called 'data' with a file in that
# folder called 'MA-PP-TOL-5-15-30-50 mg.csv'
experiment = Experiment.load_from_file(
    str(Path("data") / "MA-PP-TOL-5-15-30-50 mg.csv")
)
analyzer = Analyzer()
analyzer.add_experiment_reactors(experiment)

# plot just average transmission
fig, ax = plt.subplots(tight_layout=True)
sns.lineplot(
    x="average_temperature",
    y="average_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=ax,
)
ax.set_xlabel("Average Temperature (C)")
ax.set_ylabel("Average Transmission (%)")
plt.show()

# plot average and median transmission
fig, axes = plt.subplots(ncols=2, tight_layout=True, figsize=(12.8, 4.8))
sns.lineplot(
    x="average_temperature",
    y="average_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[0],
)
axes[0].set_xlabel("Temperature (C)")
axes[0].set_ylabel("Average Transmission (%)")

sns.lineplot(
    x="average_temperature",
    y="median_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[1],
)
axes[1].set_xlabel("Temperature (C)")
axes[1].set_ylabel("Median Transmission (%)")
plt.show()

# plot unprocessed transmission as well as processed
fig, axes = plt.subplots(nrows=2, ncols=2, tight_layout=True, figsize=(12.8, 9.6))
sns.lineplot(
    x="average_temperature",
    y="average_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[0][0],
)
axes[0][0].set_xlabel("Temperature (C)")
axes[0][0].set_ylabel("Average Transmission (%)")

sns.lineplot(
    x="average_temperature",
    y="median_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[0][1],
)
axes[0][1].set_xlabel("Temperature (C)")
axes[0][1].set_ylabel("Median Transmission (%)")

sns.lineplot(
    x="temperature",
    y="transmission",
    errorbar="sd",
    hue="reactor",
    data=analyzer.unprocessed_df,
    ax=axes[1][0],
)
axes[1][0].set_xlabel("Temperature (C)")
axes[1][0].set_ylabel("Transmission (%)")
# delete left over axes
fig.delaxes(axes[1][1])
plt.savefig(str(Path.cwd() / ".." / "images" / "experiment_one_processed.png"))
plt.close("all")
# plt.show()

# plot another experiment alongside the first
experiment2 = Experiment.load_from_file(
    str(Path("data") / "MA-PEG-TOL -5-15-30-50 mgpmL.csv")
)
analyzer.add_experiment_reactors(experiment2)

fig, axes = plt.subplots(nrows=2, ncols=2, tight_layout=True, figsize=(12.8, 9.6))
sns.lineplot(
    x="average_temperature",
    y="average_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[0][0],
)
axes[0][0].set_xlabel("Temperature (C)")
axes[0][0].set_ylabel("Average Transmission (%)")

sns.lineplot(
    x="average_temperature",
    y="median_transmission",
    hue="reactor",
    data=analyzer.df,
    ax=axes[0][1],
)
axes[0][1].set_xlabel("Temperature (C)")
axes[0][1].set_ylabel("Median Transmission (%)")

sns.lineplot(
    x="temperature",
    y="transmission",
    errorbar="sd",
    hue="reactor",
    data=analyzer.unprocessed_df,
    ax=axes[1][0],
)
axes[1][0].set_xlabel("Temperature (C)")
axes[1][0].set_ylabel("Transmission (%)")
# delete left over axes
fig.delaxes(axes[1][1])
plt.show()
