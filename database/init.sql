-- CryptoSatX Database Schema
-- PostgreSQL initialization script

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enums
CREATE TYPE signal_type AS ENUM ('LONG', 'SHORT', 'NEUTRAL');
CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE data_source AS ENUM ('coinapi', 'coinglass', 'lunarcrush', 'okx', 'smart_money');

-- Users table for authentication and preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE,
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'premium', 'enterprise')),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Signal history table
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    signal_type signal_type NOT NULL,
    score DECIMAL(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    confidence confidence_level NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    reasons JSONB NOT NULL,
    metrics JSONB NOT NULL,
    premium_metrics JSONB,
    comprehensive_metrics JSONB,
    lunarcrush_metrics JSONB,
    coinapi_metrics JSONB,
    debug_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Market data cache table
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    provider data_source NOT NULL,
    data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(symbol, provider, timestamp)
);

-- Social sentiment data table
CREATE TABLE social_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    social_score DECIMAL(5,2),
    social_volume INTEGER,
    sentiment_score DECIMAL(5,2),
    engagement_score INTEGER,
    raw_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(symbol, provider, timestamp)
);

-- API usage tracking for rate limiting
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_end TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System metrics table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backtesting results table
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20,8) NOT NULL,
    final_capital DECIMAL(20,8) NOT NULL,
    total_return DECIMAL(10,4) NOT NULL,
    max_drawdown DECIMAL(10,4) NOT NULL,
    sharpe_ratio DECIMAL(8,4),
    win_rate DECIMAL(5,4),
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    avg_win DECIMAL(20,8),
    avg_loss DECIMAL(20,8),
    profit_factor DECIMAL(8,4),
    parameters JSONB,
    trade_history JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Signal weights configuration table
CREATE TABLE signal_weights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    weight_name VARCHAR(50) NOT NULL,
    weight_value DECIMAL(5,2) NOT NULL CHECK (weight_value >= 0 AND weight_value <= 100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, weight_name)
);

-- API keys management table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    is_read BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_signals_symbol_created ON signals(symbol, created_at DESC);
CREATE INDEX idx_signals_signal_type ON signals(signal_type);
CREATE INDEX idx_signals_score ON signals(score);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);

CREATE INDEX idx_market_data_symbol_provider ON market_data(symbol, provider);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_expires_at ON market_data(expires_at);

CREATE INDEX idx_social_data_symbol ON social_data(symbol);
CREATE INDEX idx_social_data_timestamp ON social_data(timestamp DESC);
CREATE INDEX idx_social_data_expires_at ON social_data(expires_at);

CREATE INDEX idx_api_usage_user_window ON api_usage(user_id, window_start, window_end);
CREATE INDEX idx_api_usage_endpoint_window ON api_usage(endpoint, window_start, window_end);
CREATE INDEX idx_api_usage_ip_window ON api_usage(ip_address, window_start, window_end);

CREATE INDEX idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp DESC);

CREATE INDEX idx_backtest_results_user ON backtest_results(user_id);
CREATE INDEX idx_backtest_results_symbol ON backtest_results(symbol);
CREATE INDEX idx_backtest_results_created ON backtest_results(created_at DESC);

CREATE INDEX idx_signal_weights_user ON signal_weights(user_id);
CREATE INDEX idx_signal_weights_active ON signal_weights(is_active);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_read ON alerts(is_read);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signal_weights_updated_at BEFORE UPDATE ON signal_weights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW signal_summary AS
SELECT 
    symbol,
    signal_type,
    AVG(score) as avg_score,
    COUNT(*) as total_signals,
    MAX(created_at) as last_signal,
    COUNT(CASE WHEN signal_type = 'LONG' THEN 1 END) as long_count,
    COUNT(CASE WHEN signal_type = 'SHORT' THEN 1 END) as short_count,
    COUNT(CASE WHEN signal_type = 'NEUTRAL' THEN 1 END) as neutral_count
FROM signals 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY symbol, signal_type;

CREATE VIEW user_activity AS
SELECT 
    u.id,
    u.username,
    u.tier,
    COUNT(s.id) as signal_count,
    COUNT(br.id) as backtest_count,
    MAX(s.created_at) as last_signal,
    MAX(u.last_login) as last_login
FROM users u
LEFT JOIN signals s ON u.id = s.user_id
LEFT JOIN backtest_results br ON u.id = br.user_id
GROUP BY u.id, u.username, u.tier;

-- Insert default signal weights
INSERT INTO signal_weights (user_id, weight_name, weight_value) VALUES
    (NULL, 'funding_rate', 15),
    (NULL, 'social_sentiment', 10),
    (NULL, 'price_momentum', 15),
    (NULL, 'liquidations', 20),
    (NULL, 'long_short_ratio', 15),
    (NULL, 'oi_trend', 10),
    (NULL, 'smart_money', 10),
    (NULL, 'fear_greed', 5);

-- Create stored procedures for common operations
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up expired market data
    DELETE FROM market_data WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up expired social data
    DELETE FROM social_data WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Clean up old API usage records (older than 24 hours)
    DELETE FROM api_usage WHERE window_end < NOW() - INTERVAL '24 hours';
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Clean up old system metrics (older than 30 days)
    DELETE FROM system_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user's current rate limit usage
CREATE OR REPLACE FUNCTION get_user_rate_limit_usage(
    p_user_id UUID,
    p_endpoint VARCHAR,
    p_window_hours INTEGER DEFAULT 1
)
RETURNS INTEGER AS $$
DECLARE
    usage_count INTEGER;
BEGIN
    SELECT COALESCE(SUM(request_count), 0)
    INTO usage_count
    FROM api_usage
    WHERE user_id = p_user_id
    AND endpoint = p_endpoint
    AND window_start >= NOW() - INTERVAL '1 hour'
    AND window_end <= NOW();
    
    RETURN usage_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cryptosatx_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cryptosatx_user;

-- Create initial admin user (password: admin123 - change in production!)
INSERT INTO users (username, email, password_hash, tier, api_key) VALUES
('admin', 'admin@cryptosatx.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LFvOe', 'enterprise', 'csx_admin_key_2024');

COMMIT;
