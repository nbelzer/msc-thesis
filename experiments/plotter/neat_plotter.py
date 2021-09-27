import matplotlib as mpl

"""This file contains some convenience functions around matplotlib to
create good looking graphs for in research publications."""

# Recommendation by https://github.com/jbmouret/matplotlib_for_papers#a-publication-quality-figure
# See other values here: https://matplotlib.org/stable/api/matplotlib_configuration_api.html?highlight=rcparams#matplotlib.rcParams
mpl.rcParams.update({
    'axes.labelsize': 8,
    'font.size': 8,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'text.usetex': False,
    'figure.figsize': [4.5, 4.5],
    'legend.framealpha': 1,
    'grid.color': '#EEEEEE'
})
