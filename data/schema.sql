-- 资产日线数据表
CREATE TABLE IF NOT EXISTS daily_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    code TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    amount REAL,
    UNIQUE(date, code)
);

CREATE INDEX IF NOT EXISTS idx_quotes_date ON daily_quotes(date);
CREATE INDEX IF NOT EXISTS idx_quotes_code ON daily_quotes(code);
CREATE INDEX IF NOT EXISTS idx_quotes_type ON daily_quotes(asset_type);

-- 资产基本信息表
CREATE TABLE IF NOT EXISTS asset_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT,
    asset_type TEXT NOT NULL,
    market TEXT,
    list_date TEXT
);

-- 因子数据表
CREATE TABLE IF NOT EXISTS factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    code TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    value REAL,
    UNIQUE(date, code, factor_name)
);

CREATE INDEX IF NOT EXISTS idx_factors_name ON factors(factor_name);
CREATE INDEX IF NOT EXISTS idx_factors_date ON factors(date);

-- 回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    strategy_name TEXT,
    start_date TEXT,
    end_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    metrics_json TEXT,
    trades_json TEXT,
    nav_curve_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_bt_runid ON backtest_results(run_id);
