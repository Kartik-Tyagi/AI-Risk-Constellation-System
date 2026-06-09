-- PostgreSQL Schema for AI Risk Constellation System
-- This schema defines the relational database structure for portfolios,
-- transactions, market data, risk calculations, and user management.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS AND PERMISSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- PORTFOLIOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_name VARCHAR(255) NOT NULL,
    portfolio_type VARCHAR(50) NOT NULL,
    owner_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    total_value DECIMAL(20, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    inception_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_portfolios_owner ON portfolios(owner_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_type ON portfolios(portfolio_type);
CREATE INDEX IF NOT EXISTS idx_portfolios_status ON portfolios(status);

-- ============================================================================
-- PORTFOLIO POSITIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolio_positions (
    position_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id VARCHAR(50) NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    average_cost DECIMAL(20, 4),
    current_price DECIMAL(20, 4),
    market_value DECIMAL(20, 2),
    unrealized_pnl DECIMAL(20, 2),
    weight DECIMAL(5, 4),
    as_of_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON portfolio_positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_asset ON portfolio_positions(asset_id);
CREATE INDEX IF NOT EXISTS idx_positions_date ON portfolio_positions(as_of_date);

-- ============================================================================
-- TRANSACTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,
    asset_id VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 4) NOT NULL,
    total_amount DECIMAL(20, 2) NOT NULL,
    fees DECIMAL(20, 2) DEFAULT 0,
    counterparty_id VARCHAR(100),
    transaction_date TIMESTAMP NOT NULL,
    settlement_date DATE,
    status VARCHAR(50) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_transactions_asset ON transactions(asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_counterparty ON transactions(counterparty_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- ============================================================================
-- COUNTERPARTIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS counterparties (
    counterparty_id VARCHAR(100) PRIMARY KEY,
    counterparty_name VARCHAR(255) NOT NULL,
    counterparty_type VARCHAR(50) NOT NULL,
    credit_rating VARCHAR(10),
    country VARCHAR(3),
    industry VARCHAR(100),
    total_exposure DECIMAL(20, 2) DEFAULT 0,
    risk_score DECIMAL(5, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_counterparties_type ON counterparties(counterparty_type);
CREATE INDEX IF NOT EXISTS idx_counterparties_rating ON counterparties(credit_rating);
CREATE INDEX IF NOT EXISTS idx_counterparties_country ON counterparties(country);

-- ============================================================================
-- MARKET DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_data (
    market_data_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 4),
    high_price DECIMAL(20, 4),
    low_price DECIMAL(20, 4),
    close_price DECIMAL(20, 4),
    volume BIGINT,
    vwap DECIMAL(20, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_data_asset ON market_data(asset_id);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_asset_time ON market_data(asset_id, timestamp);

-- ============================================================================
-- MARKET INDICATORS
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_indicators (
    indicator_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_name VARCHAR(100) NOT NULL,
    indicator_type VARCHAR(50) NOT NULL,
    value DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_indicators_name ON market_indicators(indicator_name);
CREATE INDEX IF NOT EXISTS idx_indicators_timestamp ON market_indicators(timestamp);
CREATE INDEX IF NOT EXISTS idx_indicators_name_time ON market_indicators(indicator_name, timestamp);

-- ============================================================================
-- RISK CALCULATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS risk_calculations (
    calculation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    calculation_type VARCHAR(100) NOT NULL,
    risk_score DECIMAL(5, 4) NOT NULL,
    confidence DECIMAL(5, 4),
    var_95 DECIMAL(20, 2),
    var_99 DECIMAL(20, 2),
    expected_shortfall DECIMAL(20, 2),
    volatility DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    calculation_timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_calc_entity ON risk_calculations(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_calc_type ON risk_calculations(calculation_type);
CREATE INDEX IF NOT EXISTS idx_risk_calc_timestamp ON risk_calculations(calculation_timestamp);
CREATE INDEX IF NOT EXISTS idx_risk_calc_entity_time ON risk_calculations(entity_id, calculation_timestamp);

-- ============================================================================
-- RISK DNA
-- ============================================================================

CREATE TABLE IF NOT EXISTS risk_dna (
    dna_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    dna_vector BYTEA NOT NULL,
    dna_dimension INTEGER NOT NULL DEFAULT 256,
    generation_timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_dna_entity ON risk_dna(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_dna_timestamp ON risk_dna(generation_timestamp);

-- ============================================================================
-- RISK ALERTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS risk_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    risk_score DECIMAL(5, 4),
    threshold_breached DECIMAL(5, 4),
    alert_timestamp TIMESTAMP NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(user_id),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_entity ON risk_alerts(entity_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON risk_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON risk_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON risk_alerts(alert_timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON risk_alerts(acknowledged);

-- ============================================================================
-- MODEL METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_metadata (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    training_date TIMESTAMP,
    performance_metrics JSONB,
    hyperparameters JSONB,
    file_path TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_name ON model_metadata(model_name);
CREATE INDEX IF NOT EXISTS idx_model_type ON model_metadata(model_type);
CREATE INDEX IF NOT EXISTS idx_model_active ON model_metadata(is_active);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE OR REPLACE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_positions_updated_at BEFORE UPDATE ON portfolio_positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_counterparties_updated_at BEFORE UPDATE ON counterparties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_model_metadata_updated_at BEFORE UPDATE ON model_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Portfolio summary view
CREATE OR REPLACE VIEW portfolio_summary AS
SELECT 
    p.portfolio_id,
    p.portfolio_name,
    p.portfolio_type,
    p.total_value,
    p.currency,
    COUNT(DISTINCT pp.position_id) as num_positions,
    COUNT(DISTINCT t.transaction_id) as num_transactions,
    MAX(rc.calculation_timestamp) as last_risk_calc,
    AVG(rc.risk_score) as avg_risk_score
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.portfolio_id = pp.portfolio_id
LEFT JOIN transactions t ON p.portfolio_id = t.portfolio_id
LEFT JOIN risk_calculations rc ON p.portfolio_id::text = rc.entity_id
GROUP BY p.portfolio_id, p.portfolio_name, p.portfolio_type, p.total_value, p.currency;

-- Active alerts view
CREATE OR REPLACE VIEW active_alerts AS
SELECT 
    alert_id,
    entity_id,
    entity_type,
    alert_type,
    severity,
    message,
    risk_score,
    alert_timestamp
FROM risk_alerts
WHERE acknowledged = FALSE AND resolved = FALSE
ORDER BY severity DESC, alert_timestamp DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'System users with authentication and authorization';
COMMENT ON TABLE portfolios IS 'Investment portfolios tracked in the system';
COMMENT ON TABLE portfolio_positions IS 'Current positions within portfolios';
COMMENT ON TABLE transactions IS 'Historical transaction records';
COMMENT ON TABLE counterparties IS 'Counterparty entities and their risk profiles';
COMMENT ON TABLE market_data IS 'Historical market price and volume data';
COMMENT ON TABLE risk_calculations IS 'Historical risk calculation results';
COMMENT ON TABLE risk_dna IS 'Risk DNA fingerprints for entities';
COMMENT ON TABLE risk_alerts IS 'Risk alerts and notifications';
COMMENT ON TABLE model_metadata IS 'ML model versions and metadata';
COMMENT ON TABLE audit_log IS 'Audit trail of system actions';