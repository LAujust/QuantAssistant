"""
Drawdown Analysis Chart
"""
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd


def plot_drawdown(
    nav_series: pd.Series,
    title: str = "Drawdown Analysis",
    figsize: tuple = (12, 5),
    save_path: Optional[str] = None,
):
    """Plot drawdown filled chart"""
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax

    fig, ax = plt.subplots(figsize=figsize)
    ax.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.3, label="Drawdown")
    ax.plot(drawdown.index, drawdown, color="darkred", linewidth=1)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()
