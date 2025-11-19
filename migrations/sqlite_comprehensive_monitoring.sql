-- SQLite-compatible version of comprehensive monitoring tables
-- Run this to add new tables to existing SQLite database

-- 1. coin_watchlist table
CREATE TABLE IF NOT EXISTS coin_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    exchange TEXT DEFAULT 'binance',
    status TEXT NOT NULL DEFAULT 'active',
    priority INTEGER DEFAULT 1,
    check_interval_seconds INTEGER NOT NULL DEFAULT 300,
    timeframes TEXT,  -- JSON array as TEXT in SQLite
    metrics_enabled TEXT,  -- JSON object as TEXT in SQLite
    metadata TEXT,  -- JSON object as TEXT in SQLite
    last_check_at DATETIME,
    last_alert_at DATETIME,
    alert_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON coin_watchlist(symbol);
CREATE INDEX IF NOT EXISTS idx_watchlist_status ON coin_watchlist(status);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON coin_watchlist(priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_watchlist_last_check ON coin_watchlist(last_check_at);

-- 2. monitoring_rules table
CREATE TABLE IF NOT EXISTS monitoring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    rule_type TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    condition TEXT NOT NULL,  -- JSON object as TEXT in SQLite
    timeframe TEXT,
    priority INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,  -- Boolean as INTEGER in SQLite
    cooldown_minutes INTEGER DEFAULT 60,
    last_triggered_at DATETIME,
    trigger_count INTEGER NOT NULL DEFAULT 0,
    metadata TEXT,  -- JSON object as TEXT in SQLite
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES coin_watchlist(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rules_watchlist ON monitoring_rules(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_rules_type ON monitoring_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_rules_enabled ON monitoring_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON monitoring_rules(priority DESC, enabled);

-- 3. monitoring_alerts table
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    rule_id INTEGER,
    symbol TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    title TEXT NOT NULL,
    message TEXT,
    price REAL,
    timeframe TEXT,
    metrics TEXT,  -- JSON object as TEXT in SQLite
    analysis TEXT,  -- JSON object as TEXT in SQLite
    recommendations TEXT,  -- JSON object as TEXT in SQLite
    telegram_sent INTEGER NOT NULL DEFAULT 0,  -- Boolean as INTEGER in SQLite
    telegram_sent_at DATETIME,
    telegram_message_id TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES coin_watchlist(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES monitoring_rules(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_watchlist ON monitoring_alerts(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_alerts_rule ON monitoring_alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON monitoring_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON monitoring_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON monitoring_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON monitoring_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_telegram ON monitoring_alerts(telegram_sent, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol_created ON monitoring_alerts(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type_severity ON monitoring_alerts(alert_type, severity, created_at DESC);

-- 4. monitoring_metrics table
CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    price REAL NOT NULL,
    volume REAL,
    funding_rate REAL,
    open_interest REAL,
    liquidations_long REAL,
    liquidations_short REAL,
    social_volume INTEGER,
    metrics TEXT,  -- JSON object as TEXT in SQLite
    timestamp DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES coin_watchlist(id) ON DELETE CASCADE,
    UNIQUE(symbol, timeframe, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_metrics_watchlist ON monitoring_metrics(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_metrics_symbol ON monitoring_metrics(symbol);
CREATE INDEX IF NOT EXISTS idx_metrics_timeframe ON monitoring_metrics(timeframe);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON monitoring_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_symbol_timeframe ON monitoring_metrics(symbol, timeframe, timestamp DESC);
