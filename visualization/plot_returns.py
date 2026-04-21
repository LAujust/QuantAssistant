"""
Returns Analysis Chart: NAV Curve, Monthly/Annual Returns
"""
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_nav(
    nav_series: pd.Series,
    benchmark_series: Optional[pd.Series] = None,
    title: str = "Strategy NAV Curve",
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None,
):
    """Plot strategy NAV vs benchmark NAV"""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(nav_series.index, nav_series / nav_series.iloc[0], label="Strategy", linewidth=2)
    if benchmark_series is not None and not benchmark_series.empty:
        bench = benchmark_series.reindex(nav_series.index).dropna()
        if not bench.empty:
            ax.plot(bench.index, bench / bench.iloc[0], label="Benchmark", linewidth=1.5, linestyle="--", alpha=0.8)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative NAV")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def plot_monthly_returns(
    nav_series: pd.Series,
    title: str = "Monthly Returns",
    figsize: tuple = (14, 5),
    save_path: Optional[str] = None,
):
    """Plot monthly returns bar chart"""
    returns = nav_series.pct_change().dropna()
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    monthly.index = monthly.index.strftime("%Y-%m")

    fig, ax = plt.subplots(figsize=figsize)
    colors = ["green" if r >= 0 else "red" for r in monthly]
    ax.bar(monthly.index, monthly, color=colors, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Return")
    plt.xticks(rotation=45)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()
