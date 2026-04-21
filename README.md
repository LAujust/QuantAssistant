# MyStrategy - 量化投资策略研究平台

一个基于 **Python + SQLite** 的轻量化量化策略研究与回测框架，专为**大类资产配置**场景设计。覆盖数据获取、因子计算、策略回测、绩效分析、可视化报告的全流程。

---

## 功能特性

| 模块 | 能力 |
|------|------|
| **数据管理** | 支持 A股ETF、港股ETF、全球指数（标普500/纳斯达克/日经225）、黄金、债券等资产的日线数据获取与存储 |
| **回测引擎** | 向量化回测，支持日/周/月频调仓，内置手续费、滑点、最低佣金等 realistic 交易模型 |
| **因子系统** | 内置动量、RSI、MACD、布林带、ATR、波动率等技术因子，支持 IC/IR 分析、分层回测、相关性检测 |
| **绩效分析** | 总收益、年化收益、夏普比率、索提诺比率、最大回撤、Calmar、胜率、盈亏比、Alpha/Beta |
| **可视化** | 净值曲线、回撤填充图、月度收益柱状图、因子分布、IC序列、分层热力图、综合报告仪表盘 |
| **策略模板** | 等权重配置、动量轮动、风险平价，支持快速扩展自定义策略 |

---

## 技术栈

- **Python 3.10+**
- **SQLite** - 本地轻量级数据存储
- **akshare** - 免费金融数据接口
- **pandas / numpy** - 数据处理与数值计算
- **matplotlib** - 静态可视化（可选 seaborn 增强）
- **pytest** - 单元测试

---

## 安装

```bash
# 克隆项目后进入目录
cd MyStrategy

# 安装依赖
pip install -r requirements.txt
```

依赖清单：
- `akshare>=1.14.0`
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `matplotlib>=3.7.0`
- `pytest>=7.4.0` (开发依赖)

---

## 快速开始

### 1. 一键运行完整流程

```bash
python main.py
```

该命令会自动执行：

1. **初始化数据库** - 创建 SQLite 表结构，写入默认资产列表
2. **下载数据** - 通过 akshare 获取各资产历史日线数据（增量更新，避免重复下载）
3. **计算因子** - 批量计算动量、RSI、MACD、波动率等因子并持久化
4. **策略回测** - 运行等权重策略与动量轮动策略
5. **生成报告** - 计算绩效指标，生成可视化图表

### 2. 运行单元测试

```bash
pytest tests/ -v
```

当前覆盖 Portfolio 账户管理、Broker 交易模型、回测引擎、因子计算等核心逻辑。

---

## 项目结构

```
MyStrategy/
├── config/
│   └── settings.py              # 全局配置：资产列表、回测参数、路径
├── data/
│   ├── __init__.py
│   ├── schema.sql               # 数据库表结构定义
│   ├── storage.py               # SQLite 封装：连接池、CRUD、批量插入
│   ├── fetcher.py               # akshare 数据获取封装，支持多资产类型
│   └── manager.py               # 数据管理：增量更新、面板数据、完整性校验
├── backtest/
│   ├── __init__.py
│   ├── engine.py                # 向量化回测引擎（支持日/周/月频调仓）
│   ├── broker.py                # 模拟经纪商：市价单、手续费、滑点
│   ├── portfolio.py             # 账户与持仓管理
│   ├── metrics.py               # 绩效指标计算
│   └── report.py                # 回测报告生成与持久化
├── factor/
│   ├── __init__.py
│   ├── base.py                  # 因子抽象基类与注册器
│   ├── technical.py             # 技术因子：动量、RSI、MACD、布林带、ATR、波动率
│   ├── calculator.py            # 批量因子计算引擎
│   └── selector.py              # 因子筛选：IC/IR 分析、分层回测、相关性检测
├── visualization/
│   ├── __init__.py
│   ├── plot_returns.py          # 净值曲线、月度收益
│   ├── plot_drawdown.py         # 回撤分析图
│   ├── plot_factor.py           # 因子分布、IC序列、分层/相关性热力图
│   └── plot_report.py           # 综合报告仪表盘（2x2 子图组合）
├── strategy/
│   ├── __init__.py
│   └── template.py              # 策略模板：等权重、动量轮动、风险平价
├── utils/
│   ├── __init__.py
│   ├── logger.py                # 日志工具
│   └── helpers.py               # 通用工具（如生成唯一运行ID）
├── tests/
│   ├── __init__.py
│   ├── test_backtest.py         # 回测模块单元测试
│   └── test_factor.py           # 因子模块单元测试
├── main.py                      # 主入口：演示完整研究流程
├── requirements.txt
└── README.md
```

---

## 核心模块详解

### 数据层 (`data/`)

```python
from data.manager import DataManager

dm = DataManager()
dm.init_assets()                              # 初始化资产信息
dm.update_assets(start="20200101")            # 批量下载/更新数据
df = dm.get_data(codes=["510300", "518880"])  # 读取指定资产数据
panel = dm.get_panel_data(codes, field="close")  # 获取面板数据
```

- `Storage` 封装了 SQLite 的所有操作，支持事务、批量插入、自动建表
- `DataFetcher` 统一封装 akshare 多接口，自动处理不同资产的列名标准化
- `DataManager` 提供高层接口：增量更新、面板数据转换、数据完整性校验

### 回测层 (`backtest/`)

```python
from backtest.engine import BacktestEngine

engine = BacktestEngine(initial_cash=1_000_000)
result = engine.run(price_df, signal_df, rebalance_freq="M")
# result 包含：nav_series(净值序列), trades(交易记录), final_portfolio(最终持仓)
```

- **向量化引擎**：基于 pandas 矩阵运算，适合快速验证想法
- **交易模型**：手续费率 + 最低佣金 + 滑点，贴近真实交易
- **绩效指标**：年化收益、夏普、索提诺、最大回撤、Calmar、胜率、盈亏比、Alpha/Beta

### 因子层 (`factor/`)

```python
from factor.calculator import FactorCalculator
from factor.selector import FactorSelector

# 批量计算并存储因子
fc = FactorCalculator()
fc.calculate_and_save(codes=["510300", "518880"], factor_names=["momentum_20", "rsi"])

# IC 分析
fs = FactorSelector()
ic_stats = fs.ic_analysis("momentum_20", codes)
# {'mean_ic': 0.05, 'ic_std': 0.15, 'ir': 0.33, 'ic_positive_ratio': 0.55}

# 分层回测
layer_returns = fs.layer_backtest("momentum_20", codes, n_layers=5)
```

- 内置因子通过装饰器注册到 `FactorRegistry`，扩展方便
- `FactorSelector` 提供 IC/IR 分析、分层回测（检验因子单调性）、因子相关性检测

### 可视化层 (`visualization/`)

```python
from visualization.plot_returns import plot_nav, plot_monthly_returns
from visualization.plot_drawdown import plot_drawdown
from visualization.plot_report import generate_report_chart

# 综合报告（2x2子图：净值、回撤、月度收益、指标文本）
generate_report_chart(nav_series, benchmark_series, metrics=metrics, save_path="report.png")
```

- 所有图表均支持 `save_path` 参数保存为 PNG
- seaborn 为可选依赖，未安装时自动回退到 matplotlib

---

## 自定义策略

继承 `BaseStrategy` 并实现 `generate_weights` 方法即可：

```python
from strategy.template import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    """
    示例：双均线轮动策略
    持有短期均线上穿长期均线的资产，等权配置
    """
    def __init__(self, short=20, long=60, top_n=3):
        self.short = short
        self.long = long
        self.top_n = top_n

    def generate_weights(self, price_df: pd.DataFrame, current_date: pd.Timestamp, **kwargs):
        hist = price_df.loc[:current_date]
        if len(hist) < self.long:
            # 数据不足，等权
            n = len(price_df.columns)
            return pd.Series(1.0 / n, index=price_df.columns)

        ma_short = hist.iloc[-self.short:].mean()
        ma_long = hist.iloc[-self.long:].mean()
        signal = (ma_short > ma_long).astype(float)

        # 选取信号最强的 top_n
        selected = signal.nlargest(self.top_n).index
        weights = pd.Series(0.0, index=price_df.columns)
        weights.loc[selected] = 1.0 / len(selected)
        return weights
```

然后在 `main.py` 中使用：

```python
strategy = MyStrategy(short=20, long=60, top_n=3)
signal_df = build_signal_df(price_df, strategy)
engine = BacktestEngine()
result = engine.run(price_df, signal_df, rebalance_freq="M")
```

---

## 数据库表结构

| 表名 | 说明 | 核心字段 |
|------|------|----------|
| `daily_quotes` | 资产日线行情 | `date`, `code`, `asset_type`, `open`, `high`, `low`, `close`, `volume` |
| `asset_info` | 资产基本信息 | `code`, `name`, `asset_type`, `market`, `list_date` |
| `factors` | 因子数据 | `date`, `code`, `factor_name`, `value` |
| `backtest_results` | 回测结果 | `run_id`, `strategy_name`, `metrics_json`, `trades_json`, `nav_curve_json` |

---

## 默认关注资产

配置在 `config/settings.py` 中，可根据需要修改：

| 资产 | 代码 | 类型 |
|------|------|------|
| 沪深300ETF | 510300 | A股ETF |
| 中证500ETF | 510500 | A股ETF |
| 科创50ETF | 588000 | A股ETF |
| 创业板ETF | 159915 | A股ETF |
| H股ETF | 510900 | 港股ETF |
| 恒生ETF | 159920 | 港股ETF |
| 标普500 | SPX | 全球指数 |
| 纳斯达克 | IXIC | 全球指数 |
| 日经225 | N225 | 全球指数 |
| 黄金ETF | 518880 | 商品 |
| 国债ETF | 511010 | 债券 |

---

## 注意事项

1. **数据源**：akshare 为免费数据源，接口可能因网络或数据源变更而波动。如遇获取失败，请检查 akshare 版本并参考其 [官方文档](https://www.akshare.xyz/)
2. **全球指数**：美股、日经等数据依赖 akshare 特定接口，部分数据可能存在延迟或缺失，建议以 A股ETF 为主要研究对象
3. **回测模式**：当前为向量化回测，假设调仓日收盘价成交，适合中长期策略验证。如需 tick 级别或复杂事件驱动逻辑，可扩展 `backtest/engine.py`
4. **性能**：SQLite 足以支撑万级数据量的本地研究。如数据规模扩大，可平滑迁移至 PostgreSQL（仅需替换 `Storage` 类）
5. **风险提示**：本框架仅供研究与学习使用，不构成任何投资建议。回测表现不代表未来收益
