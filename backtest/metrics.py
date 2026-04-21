"""
绩效指标计算
"""
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def calculate_metrics(
    nav_series: pd.Series,
    benchmark_series: Optional[pd.Series] = None,
    risk_free_rate: float = 0.03,
) -> Dict[str, float]:
    """
    计算回测绩效指标
    nav_series: 每日净值序列 (index=date, values=nav)
    benchmark_series: 基准每日净值序列（可选）
    risk_free_rate: 无风险利率（年化）
    """
    if nav_series.empty or len(nav_series) < 2:
        return {}

    nav = nav_series.dropna()
    returns = nav.pct_change().dropna()
    total_return = nav.iloc[-1] / nav.iloc[0] - 1
    n_years = len(nav) / 252
    annual_return = (1 + total_return) ** (1 / max(n_years, 1e-6)) - 1

    # 波动率
    volatility = returns.std() * np.sqrt(252)

    # 夏普比率
    sharpe = (annual_return - risk_free_rate) / volatility if volatility != 0 else np.nan

    # 索提诺比率（下行波动率）
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0
    sortino = (annual_return - risk_free_rate) / downside_std if downside_std != 0 else np.nan

    # 最大回撤
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_drawdown = drawdown.min()
    max_dd_end = drawdown.idxmin()
    max_dd_start = nav.loc[:max_dd_end].idxmax()
    dd_duration = (max_dd_end - max_dd_start).days

    # Calmar 比率
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else np.nan

    # 胜率、盈亏比
    win_rate = (returns > 0).mean()
    avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
    avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss != 0 else np.nan

    metrics = {
        "total_return": round(total_return, 4),
        "annual_return": round(annual_return, 4),
        "volatility": round(volatility, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown": round(max_drawdown, 4),
        "max_dd_start": str(max_dd_start)[:10],
        "max_dd_end": str(max_dd_end)[:10],
        "max_dd_duration": dd_duration,
        "calmar_ratio": round(calmar, 4),
        "win_rate": round(win_rate, 4),
        "profit_loss_ratio": round(profit_loss_ratio, 4),
    }

    # 相对基准指标
    if benchmark_series is not None and not benchmark_series.empty:
        bench = benchmark_series.reindex(nav.index).dropna()
        if len(bench) > 1:
            bench_returns = bench.pct_change().dropna()
            common_index = returns.index.intersection(bench_returns.index)
            r = returns.loc[common_index]
            br = bench_returns.loc[common_index]
            # 阿尔法、贝塔
            cov = np.cov(r, br)[0, 1]
            var = br.var()
            beta = cov / var if var != 0 else np.nan
            alpha = (r.mean() - beta * br.mean()) * 252 if not np.isnan(beta) else np.nan
            # 信息比率
            tracking_error = (r - br).std() * np.sqrt(252)
            info_ratio = (r.mean() - br.mean()) * 252 / tracking_error if tracking_error != 0 else np.nan
            metrics["alpha"] = round(alpha, 4)
            metrics["beta"] = round(beta, 4)
            metrics["info_ratio"] = round(info_ratio, 4)

    return metrics


def max_drawdown_series(nav: pd.Series) -> pd.Series:
    """返回回撤序列"""
    cummax = nav.cummax()
    return (nav - cummax) / cummax
