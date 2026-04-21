"""
Comprehensive Report Dashboard: Generate Multi-Plot Combo with One Click
"""
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd

from visualization.plot_drawdown import plot_drawdown
from visualization.plot_returns import plot_nav, plot_monthly_returns


def generate_report_chart(
    nav_series: pd.Series,
    benchmark_series: Optional[pd.Series] = None,
    metrics: Optional[Dict] = None,
    save_path: Optional[str] = None,
):
    """
    Generate comprehensive report chart (2x2 subplots)
    """
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)

    # 1. NAV Curve
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(nav_series.index, nav_series / nav_series.iloc[0], label="Strategy", linewidth=2)
    if benchmark_series is not None and not benchmark_series.empty:
        bench = benchmark_series.reindex(nav_series.index).dropna()
        if not bench.empty:
            ax1.plot(bench.index, bench / bench.iloc[0], label="Benchmark", linewidth=1.5, linestyle="--", alpha=0.8)
    ax1.set_title("Strategy NAV Curve", fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Drawdown
    ax2 = fig.add_subplot(gs[1, 0])
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax
    ax2.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.3)
    ax2.plot(drawdown.index, drawdown, color="darkred", linewidth=1)
    ax2.set_title("Drawdown Curve", fontsize=12)
    ax2.grid(True, alpha=0.3)

    # 3. Monthly Returns
    ax3 = fig.add_subplot(gs[1, 1])
    returns = nav_series.pct_change().dropna()
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    colors = ["green" if r >= 0 else "red" for r in monthly]
    ax3.bar(monthly.index.strftime("%Y-%m"), monthly, color=colors, alpha=0.7)
    ax3.axhline(0, color="black", linewidth=0.5)
    ax3.set_title("Monthly Returns", fontsize=12)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 4. Metrics
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis("off")
    if metrics:
        text_lines = [
            f"Total Return: {metrics.get('total_return', 0):.2%}",
            f"Annual Return: {metrics.get('annual_return', 0):.2%}",
            f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}",
            f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}",
            f"Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}",
            f"Win Rate: {metrics.get('win_rate', 0):.2%}",
            f"Profit/Loss Ratio: {metrics.get('profit_loss_ratio', 0):.2f}",
        ]
        text = "  |  ".join(text_lines)
        ax4.text(0.5, 0.5, text, transform=ax4.transAxes, fontsize=12,
                 verticalalignment="center", horizontalalignment="center",
                 bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    else:
        ax4.text(0.5, 0.5, "No metrics data available", transform=ax4.transAxes, fontsize=12,
                 verticalalignment="center", horizontalalignment="center")

    plt.suptitle("Quantitative Strategy Backtest Report", fontsize=16, y=0.98)
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
