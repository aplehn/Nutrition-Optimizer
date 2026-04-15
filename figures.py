import matplotlib.pyplot as plt
import numpy as np


def plot_nutrient_comparison(
    baseline_totals,
    satiety_totals,
    nutrients_to_plot=None,
    title="Nutrient Comparison: Baseline vs Satiety"
):
    """
    Create a grouped bar chart comparing nutrient totals from two optimizer runs.

    Parameters
    ----------
    baseline_totals : dict
        Nutrient totals from baseline optimizer run.
    satiety_totals : dict
        Nutrient totals from satiety-based optimizer run.
    nutrients_to_plot : list[str] or None
        Nutrients to include in the figure. If None, uses common keys.
    title : str
        Figure title.
    """

    # Use overlapping nutrients unless a specific list is provided
    if nutrients_to_plot is None:
        nutrients_to_plot = [
            nutrient for nutrient in baseline_totals.keys()
            if nutrient in satiety_totals
        ]

    baseline_values = [baseline_totals[n] for n in nutrients_to_plot]
    satiety_values = [satiety_totals[n] for n in nutrients_to_plot]

    x = np.arange(len(nutrients_to_plot))
    width = 0.38

    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, baseline_values, width, label="Baseline")
    plt.bar(x + width/2, satiety_values, width, label="Satiety")

    plt.xticks(x, nutrients_to_plot, rotation=45, ha='right')
    plt.ylabel("Total Intake")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()