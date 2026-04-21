"""
全局配置文件
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 数据目录
DATA_DIR = PROJECT_ROOT / "data_files"
DATA_DIR.mkdir(exist_ok=True)

# SQLite 数据库路径
DB_PATH = DATA_DIR / "quant.db"

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 回测默认参数
BACKTEST_CONFIG = {
    "initial_cash": 1_000_000.0,      # 初始资金
    "commission_rate": 0.0003,        # 手续费率 (万3)
    "min_commission": 5.0,            # 最低手续费
    "slippage": 0.001,                # 滑点比例 (0.1%)
    "start_date": "2020-01-01",       # 默认回测开始日期
    "end_date": "2026-04-10",         # 默认回测结束日期
    "benchmark": "000300.SH",         # 默认基准：沪深300
}

# 资产类型定义
ASSET_TYPES = {
    "a_share_etf": "A股ETF",
    "hk_etf": "港股ETF",
    "global_index": "全球指数",
    "commodity": "商品",
    "bond": "债券",
}

# 默认关注的资产列表（示例）
DEFAULT_ASSETS = [
    # A股宽基ETF
    {"code": "510300", "name": "沪深300ETF", "asset_type": "a_share_etf", "market": "SH"},
    {"code": "510500", "name": "中证500ETF", "asset_type": "a_share_etf", "market": "SH"},
    {"code": "588000", "name": "科创50ETF", "asset_type": "a_share_etf", "market": "SH"},
    {"code": "159915", "name": "创业板ETF", "asset_type": "a_share_etf", "market": "SZ"},
    # 港股ETF
    {"code": "510900", "name": "H股ETF", "asset_type": "hk_etf", "market": "SH"},
    {"code": "159920", "name": "恒生ETF", "asset_type": "hk_etf", "market": "SZ"},
    # 全球指数 (通过akshare对应的指数代码)
    {"code": ".INX", "name": "标普500", "asset_type": "global_index", "market": "US"},
    {"code": ".IXIC", "name": "纳斯达克", "asset_type": "global_index", "market": "US"},
    {"code": "NKY", "name": "日经225", "asset_type": "global_index", "market": "JP"},
    # 黄金
    {"code": "518880", "name": "黄金ETF", "asset_type": "commodity", "market": "SH"},
    # 债券
    {"code": "511010", "name": "国债ETF", "asset_type": "bond", "market": "SH"},
]
