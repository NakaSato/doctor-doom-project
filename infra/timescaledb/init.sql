-- TimescaleDB Telemetry Schema
-- Module telemetry time-series data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ==================== Module Telemetry ====================
CREATE TABLE IF NOT EXISTS module_telemetry (
    timestamp TIMESTAMPTZ NOT NULL,
    module_id VARCHAR(50) NOT NULL,
    temperature DECIMAL(8, 2),  -- Celsius
    power_output_w DECIMAL(8, 2),  -- Watts
    voltage_v DECIMAL(8, 2),
    current_a DECIMAL(8, 2),
    efficiency DECIMAL(6, 4),  -- 0.0 to 1.0
    irradiance_w_m2 DECIMAL(8, 2),
    ambient_temperature DECIMAL(8, 2),
    wind_speed_m_s DECIMAL(6, 2),
    metadata JSONB DEFAULT '{}'
);

-- Convert to hypertable
SELECT create_hypertable('module_telemetry', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_module_telemetry_module_id ON module_telemetry(module_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_module_telemetry_timestamp ON module_telemetry(timestamp DESC);

-- Create compression policy (compress data older than 7 days)
SELECT add_compression_policy('module_telemetry', INTERVAL '7 days', if_not_exists => TRUE);

-- Create retention policy (drop data older than 2 years)
-- SELECT add_retention_policy('module_telemetry', INTERVAL '2 years', if_not_exists => TRUE);

-- ==================== Continuous Aggregates ====================

-- Hourly averages
CREATE MATERIALIZED VIEW IF NOT EXISTS module_telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
    module_id,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(temperature) AS avg_temperature,
    AVG(power_output_w) AS avg_power_output,
    AVG(efficiency) AS avg_efficiency,
    AVG(irradiance_w_m2) AS avg_irradiance,
    MAX(temperature) AS max_temperature,
    MIN(temperature) AS min_temperature
FROM module_telemetry
GROUP BY module_id, bucket
WITH NO DATA;

-- Daily aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS module_telemetry_daily
WITH (timescaledb.continuous) AS
SELECT
    module_id,
    time_bucket('1 day', timestamp) AS bucket,
    AVG(temperature) AS avg_temperature,
    SUM(power_output_w) AS total_power_output,
    AVG(efficiency) AS avg_efficiency,
    AVG(irradiance_w_m2) AS avg_irradiance,
    MAX(temperature) AS max_temperature,
    MIN(temperature) AS min_temperature
FROM module_telemetry
GROUP BY module_id, bucket
WITH NO DATA;

-- Refresh policies
SELECT add_continuous_aggregate_policy('module_telemetry_hourly',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '10 minutes',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('module_telemetry_daily',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);
