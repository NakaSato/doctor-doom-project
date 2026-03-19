-- Doctor Doom Database Schema
-- PostgreSQL + PostGIS initialization script

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==================== Sites ====================
CREATE TABLE IF NOT EXISTS sites (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location GEOMETRY(POLYGON, 4326) NOT NULL,
    area_hectares DECIMAL(10, 2) NOT NULL,
    module_count INTEGER NOT NULL DEFAULT 0,
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sites_location ON sites USING GIST(location);
CREATE INDEX idx_sites_status ON sites(status);

-- ==================== Modules ====================
CREATE TABLE IF NOT EXISTS modules (
    id VARCHAR(50) PRIMARY KEY,
    site_id VARCHAR(50) NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    position GEOMETRY(POINT, 4326) NOT NULL,
    orientation DECIMAL(5, 2) DEFAULT 0,  -- degrees from north
    tilt DECIMAL(5, 2) DEFAULT 30,  -- degrees from horizontal
    rated_power_w DECIMAL(8, 2) NOT NULL,
    cell_count INTEGER DEFAULT 60,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(100),
    installed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_modules_site_id ON modules(site_id);
CREATE INDEX idx_modules_position ON modules USING GIST(position);
CREATE INDEX idx_modules_status ON modules(status);

-- ==================== Inspections ====================
CREATE TABLE IF NOT EXISTS inspections (
    id VARCHAR(50) PRIMARY KEY,
    site_id VARCHAR(50) NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    drone_id VARCHAR(50) NOT NULL,
    pilot_id VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    image_count INTEGER DEFAULT 0,
    flight_path GEOMETRY(LINESTRING, 4326),
    weather_conditions JSONB,
    status VARCHAR(50) DEFAULT 'in_progress',  -- in_progress, completed, failed
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_inspections_site_id ON inspections(site_id);
CREATE INDEX idx_inspections_status ON inspections(status);
CREATE INDEX idx_inspections_started_at ON inspections(started_at);

-- ==================== Thermal Images ====================
CREATE TABLE IF NOT EXISTS thermal_images (
    id VARCHAR(50) PRIMARY KEY,
    inspection_id VARCHAR(50) NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    module_id VARCHAR(50) REFERENCES modules(id),
    image_path VARCHAR(500) NOT NULL,
    s3_key VARCHAR(500),
    minio_bucket VARCHAR(100) DEFAULT 'thermal-images',
    capture_time TIMESTAMP WITH TIME ZONE NOT NULL,
    gps_location GEOMETRY(POINT, 4326),
    altitude_m DECIMAL(8, 2),
    camera_angle DECIMAL(5, 2),
    thermal_metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_thermal_images_inspection_id ON thermal_images(inspection_id);
CREATE INDEX idx_thermal_images_module_id ON thermal_images(module_id);
CREATE INDEX idx_thermal_images_gps ON thermal_images USING GIST(gps_location);
CREATE INDEX idx_thermal_images_processed ON thermal_images(processed);

-- ==================== Defects ====================
CREATE TABLE IF NOT EXISTS defects (
    id VARCHAR(50) PRIMARY KEY,
    module_id VARCHAR(50) NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    inspection_id VARCHAR(50) REFERENCES inspections(id),
    defect_type VARCHAR(100) NOT NULL,  -- hotspot, cell_anomaly, delamination, etc.
    severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    confidence DECIMAL(5, 4) NOT NULL,  -- 0.0 to 1.0
    location GEOMETRY(POINT, 4326),
    bounding_box JSONB,  -- [x1, y1, x2, y2]
    temperature_delta DECIMAL(8, 2),  -- ΔT in Celsius
    max_temperature DECIMAL(8, 2),
    ambient_temperature DECIMAL(8, 2),
    ml_model_version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'detected',  -- detected, reviewed, resolved, false_positive
    reviewer_id VARCHAR(50),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_defects_module_id ON defects(module_id);
CREATE INDEX idx_defects_inspection_id ON defects(inspection_id);
CREATE INDEX idx_defects_location ON defects USING GIST(location);
CREATE INDEX idx_defects_severity ON defects(severity);
CREATE INDEX idx_defects_status ON defects(status);
CREATE INDEX idx_defects_detected_at ON defects(detected_at);

-- ==================== Reports ====================
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(50) PRIMARY KEY,
    site_id VARCHAR(50) NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    inspection_id VARCHAR(50) REFERENCES inspections(id),
    report_type VARCHAR(50) DEFAULT 'inspection',  -- inspection, summary, compliance
    format VARCHAR(20) DEFAULT 'pdf',  -- pdf, html, json
    s3_key VARCHAR(500),
    minio_bucket VARCHAR(100) DEFAULT 'reports',
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, generating, completed, failed
    generated_by VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reports_site_id ON reports(site_id);
CREATE INDEX idx_reports_inspection_id ON reports(inspection_id);
CREATE INDEX idx_reports_status ON reports(status);

-- ==================== Users ====================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'operator',  -- operator, admin, super_admin
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ==================== Token Blacklist (for logout) ====================
CREATE TABLE IF NOT EXISTS token_blacklist (
    id VARCHAR(50) PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);

-- ==================== Audit Log ====================
CREATE TABLE IF NOT EXISTS audit_log (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ==================== Functions & Triggers ====================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_modules_updated_at BEFORE UPDATE ON modules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-increment module_count on sites
CREATE OR REPLACE FUNCTION increment_module_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sites SET module_count = module_count + 1 WHERE id = NEW.site_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_increment_module_count AFTER INSERT ON modules
    FOR EACH ROW EXECUTE FUNCTION increment_module_count();

-- ==================== Initial Data ====================

-- Create default admin user (password: admin123)
INSERT INTO users (id, email, password_hash, full_name, role)
VALUES (
    'usr_admin_001',
    'admin@doctor-doom.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
    'System Administrator',
    'super_admin'
) ON CONFLICT (email) DO NOTHING;
