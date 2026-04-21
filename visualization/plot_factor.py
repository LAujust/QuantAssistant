"""
Factor Visualization: Distribution, IC Series, Layer Heatmap, Correlation
seaborn is an optional dependency, falls back to matplotlib if not installed
"""
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import seaborn as sns
    _HAS_SEABORN = True
except Exception:
    _HAS_SEABORN = False


def plot_factor_dist(
    factor_values: pd.Series,
    title: str = "Factor Distribution",
    figsize: tuple = (10, 5),
    save_path: Optional[str] = None,
):
    """Factor value distribution histogram + KDE (optional)"""
    fig, ax = plt.subplots(figsize=figsize)
    vals = factor_values.dropna()
    ax.hist(vals, bins=50, color="steelblue", alpha=0.6, density=True, label="Distribution")
    if _HAS_SEABORN:
        try:
            sns.kdeplot(vals, ax=ax, color="darkblue", linewidth=2, label="KDE")
        except Exception:
            pass
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Factor Value")
    ax.set_ylabel("Density")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def plot_ic_series(
    ic_series: pd.Series,
    title: str = "IC Series",
    figsize: tuple = (12, 4),
    save_path: Optional[str] = None,
):
    """Plot IC time series"""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(ic_series.index, ic_series, linewidth=1.2, color="steelblue")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(ic_series.mean(), color="red", linestyle="--", label=f"Mean={ic_series.mean():.3f}")
    ax.fill_between(ic_series.index, ic_series, 0, where=(ic_series > 0), color="green", alpha=0.2)
    ax.fill_between(ic_series.index, ic_series, 0, where=(ic_series < 0), color="red", alpha=0.2)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("IC")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def _plot_heatmap_matplotlib(data: pd.DataFrame, ax, cmap: str = "RdYlGn", vmin=None, vmax=None, fmt=".2%"):
    """Plot heatmap using matplotlib (fallback when seaborn is unavailable)"""
    im = ax.imshow(data.values, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(data.columns)))
    ax.set_yticks(range(len(data.index)))
    ax.set_xticklabels(data.columns, rotation=45, ha="right")
    ax.set_yticklabels(data.index)
    # Annotate values
    for i in range(len(data.index)):
        for j in range(len(data.columns)):
            val = data.iloc[i, j]
            text = f"{val:.2%}" if fmt == ".2%" else f"{val:.2f}"
            ax.text(j, i, text, ha="center", va="center", color="black", fontsize=8)
    plt.colorbar(im, ax=ax)


def plot_layer_heatmap(
    layer_returns: pd.DataFrame,
    title: str = "Layer Returns Heatmap",
    figsize: tuple = (10, 6),
    save_path: Optional[str] = None,
):
    """Layer returns monthly cumulative heatmap"""
    monthly = layer_returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    monthly.index = monthly.index.strftime("%Y-%m")

    fig, ax = plt.subplots(figsize=figsize)
    if _HAS_SEABORN:
        sns.heatmap(monthly.T, cmap="RdYlGn", center=0, annot=True, fmt=".2%", linewidths=0.5, ax=ax)
    else:
        _plot_heatmap_matplotlib(monthly.T, ax, cmap="RdYlGn", vmin=-0.15, vmax=0.15)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Layer")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def plot_factor_corr(
    corr_matrix: pd.DataFrame,
    title: str = "Factor Correlation Heatmap",
    figsize: tuple = (8, 6),
    save_path: Optional[str] = None,
):
    """Plot factor correlation heatmap"""
    fig, ax = plt.subplots(figsize=figsize)
    if _HAS_SEABORN:
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        sns.heatmap(corr_matrix, mask=mask, cmap="coolwarm", center=0, annot=True, fmt=".2f",
                    square=True, linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    else:
        _plot_heatmap_matplotlib(corr_matrix, ax, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f")
    ax.set_title(title, fontsize=14)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()
