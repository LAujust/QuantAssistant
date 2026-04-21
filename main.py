"""
主入口：演示完整量化流程
1. 初始化数据库 & 下载数据
2. 计算因子
3. 回测策略
4. 生成可视化报告
"""
import pandas as pd

from backtest.engine import BacktestEngine
from backtest.metrics import calculate_metrics
from backtest.report import Report
from config.settings import BACKTEST_CONFIG, DEFAULT_ASSETS
from data.manager import DataManager
from factor.calculator import FactorCalculator
from strategy.template import MomentumRotationStrategy, EqualWeightStrategy
from utils.helpers import generate_run_id
from utils.logger import get_logger
from visualization.plot_report import generate_report_chart

logger = get_logger("main")


def build_signal_df(price_df: pd.DataFrame, strategy, rebalance_dates) -> pd.DataFrame:
    """根据策略生成信号权重 DataFrame"""
    signals = []
    for date in price_df.index:
        weights = strategy.generate_weights(price_df, date)
        signals.append(weights)
    signal_df = pd.DataFrame(signals, index=price_df.index).fillna(0)
    return signal_df


def run_pipeline():
    run_id = generate_run_id()
    logger.info(f"=== 量化策略回测开始 | RunID: {run_id} ===")

    # --------------------------------------------------
    # Step 1: 数据准备
    # --------------------------------------------------
    logger.info("Step 1: 初始化数据管理器并更新数据...")
    dm = DataManager()
    dm.init_assets()

    # 下载数据（如已存在则增量更新）
    start = "20200101"
    end = "20241231"
    dm.update_assets(start=start, end=end)

    # 读取数据
    codes = [a["code"] for a in DEFAULT_ASSETS]
    df = dm.get_data(codes=codes, start="2020-01-01", end="2024-12-31")
    if df.empty:
        logger.error("数据库中无数据，请检查数据下载是否成功")
        return

    price_df = df.pivot(index="date", columns="code", values="close").sort_index()
    price_df = price_df.dropna(how="all", axis=1).dropna(how="all", axis=0)
    codes = price_df.columns.tolist()
    logger.info(f"数据加载完成，共 {len(codes)} 个资产，{len(price_df)} 个交易日")

    # --------------------------------------------------
    # Step 2: 因子计算（可选，用于策略或分析）
    # --------------------------------------------------
    logger.info("Step 2: 计算因子...")
    fc = FactorCalculator()
    factor_names = ["momentum_20", "momentum_60", "rsi", "volatility"]
    fc.calculate_and_save(codes, factor_names)
    logger.info(f"因子计算完成: {factor_names}")

    # --------------------------------------------------
    # Step 3: 回测
    # --------------------------------------------------
    logger.info("Step 3: 执行回测...")

    # 策略A: 等权重
    strategy_eq = EqualWeightStrategy()
    signal_eq = build_signal_df(price_df, strategy_eq, None)
    engine_eq = BacktestEngine(initial_cash=BACKTEST_CONFIG["initial_cash"])
    result_eq = engine_eq.run(price_df, signal_eq, rebalance_freq="M")

    # 策略B: 动量轮动
    strategy_mom = MomentumRotationStrategy(lookback=60, top_n=3)
    signal_mom = build_signal_df(price_df, strategy_mom, None)
    engine_mom = BacktestEngine(initial_cash=BACKTEST_CONFIG["initial_cash"])
    result_mom = engine_mom.run(price_df, signal_mom, rebalance_freq="M")

    # 基准: 等权买入持有
    benchmark_nav = (price_df.pct_change().mean(axis=1) + 1).cumprod() * BACKTEST_CONFIG["initial_cash"]

    logger.info(f"回测完成，等权策略最终净值: {result_eq['nav_series'].iloc[-1]:,.2f}")
    logger.info(f"动量轮动策略最终净值: {result_mom['nav_series'].iloc[-1]:,.2f}")

    # --------------------------------------------------
    # Step 4: 报告与可视化
    # --------------------------------------------------
    logger.info("Step 4: 生成报告与可视化...")
    reporter = Report()

    # 等权重策略报告
    metrics_eq = calculate_metrics(result_eq["nav_series"], benchmark_nav)
    report_eq = reporter.generate(
        run_id=run_id + "_eq",
        strategy_name="EqualWeight",
        start_date=str(price_df.index[0])[:10],
        end_date=str(price_df.index[-1])[:10],
        nav_series=result_eq["nav_series"],
        trades=result_eq["trades"],
        benchmark_series=benchmark_nav,
    )
    logger.info(f"等权策略指标: {metrics_eq}")

    # 动量轮动策略报告
    metrics_mom = calculate_metrics(result_mom["nav_series"], benchmark_nav)
    report_mom = reporter.generate(
        run_id=run_id + "_mom",
        strategy_name="MomentumRotation",
        start_date=str(price_df.index[0])[:10],
        end_date=str(price_df.index[-1])[:10],
        nav_series=result_mom["nav_series"],
        trades=result_mom["trades"],
        benchmark_series=benchmark_nav,
    )
    logger.info(f"动量轮动策略指标: {metrics_mom}")

    # 可视化
    from visualization.plot_returns import plot_nav
    from visualization.plot_drawdown import plot_drawdown

    plot_nav(result_mom["nav_series"], benchmark_nav, title="动量轮动策略 vs 基准")
    plot_drawdown(result_mom["nav_series"], title="动量轮动策略回撤")
    generate_report_chart(
        result_mom["nav_series"],
        benchmark_nav,
        metrics=metrics_mom,
        save_path=f"logs/report_{run_id}.png",
    )

    logger.info(f"=== 全部完成，报告已保存 | RunID: {run_id} ===")


if __name__ == "__main__":
    run_pipeline()
