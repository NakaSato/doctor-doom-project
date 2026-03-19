-- Doctor Doom Database Seed Data
-- Run after initial schema setup for demo/testing purposes

-- ==================== Sites ====================
INSERT INTO sites (id, name, location, area_hectares, module_count, address, city, country, status) VALUES
('site_001', 'Solar Farm Alpha', 
 ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[100.5,13.7],[100.51,13.7],[100.51,13.71],[100.5,13.71],[100.5,13.7]]]}'),
 50.0, 0, '123 Solar Street', 'Bangkok', 'Thailand', 'active'),
('site_002', 'Solar Farm Beta',
 ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[100.52,13.72],[100.53,13.72],[100.53,13.73],[100.52,13.73],[100.52,13.72]]]}'),
 35.0, 0, '456 Energy Avenue', 'Bangkok', 'Thailand', 'active'),
('site_003', 'Rooftop Installation Gamma',
 ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[100.54,13.74],[100.545,13.74],[100.545,13.745],[100.54,13.745],[100.54,13.74]]]}'),
 5.0, 0, '789 Green Road', 'Bangkok', 'Thailand', 'active');

-- ==================== Modules ====================
-- Site 001 - 20 modules in a grid pattern
INSERT INTO modules (id, site_id, position, orientation, tilt, rated_power_w, cell_count, manufacturer, model, status)
SELECT 
    'mod_001_' || i,
    'site_001',
    ST_GeomFromGeoJSON('{"type":"Point","coordinates":[' || (100.5 + (i % 5) * 0.001) || ',' || (13.7 + floor(i / 5) * 0.001) || ']}'),
    180.0,
    30.0,
    400.0,
    72,
    'SolarTech',
    'ST-400M',
    'active'
FROM generate_series(1, 20) AS i;

-- Site 002 - 15 modules
INSERT INTO modules (id, site_id, position, orientation, tilt, rated_power_w, cell_count, manufacturer, model, status)
SELECT 
    'mod_002_' || i,
    'site_002',
    ST_GeomFromGeoJSON('{"type":"Point","coordinates":[' || (100.52 + (i % 5) * 0.001) || ',' || (13.72 + floor(i / 5) * 0.001) || ']}'),
    175.0,
    25.0,
    350.0,
    60,
    'SunPower',
    'SP-350X',
    'active'
FROM generate_series(1, 15) AS i;

-- Site 003 - 8 modules
INSERT INTO modules (id, site_id, position, orientation, tilt, rated_power_w, cell_count, manufacturer, model, status)
SELECT 
    'mod_003_' || i,
    'site_003',
    ST_GeomFromGeoJSON('{"type":"Point","coordinates":[' || (100.54 + (i % 4) * 0.001) || ',' || (13.74 + floor(i / 4) * 0.001) || ']}'),
    185.0,
    20.0,
    300.0,
    60,
    'LG Solar',
    'LG-300N',
    'active'
FROM generate_series(1, 8) AS i;

-- ==================== Inspections ====================
INSERT INTO inspections (id, site_id, drone_id, pilot_id, started_at, completed_at, image_count, status) VALUES
('insp_001', 'site_001', 'drone_mavic3t_01', 'pilot_001', 
 '2026-03-15 09:00:00+00', '2026-03-15 10:30:00+00', 20, 'completed'),
('insp_002', 'site_002', 'drone_mavic3t_01', 'pilot_001',
 '2026-03-16 10:00:00+00', '2026-03-16 11:00:00+00', 15, 'completed'),
('insp_003', 'site_003', 'drone_mavic3t_02', 'pilot_002',
 '2026-03-17 14:00:00+00', '2026-03-17 14:45:00+00', 8, 'completed'),
('insp_004', 'site_001', 'drone_mavic3t_01', 'pilot_001',
 '2026-03-18 09:00:00+00', NULL, 0, 'in_progress');

-- ==================== Defects ====================
-- Various defects with different severities
INSERT INTO defects (id, module_id, inspection_id, defect_type, severity, confidence, location, temperature_delta, max_temperature, ambient_temperature, status) VALUES
('def_001', 'mod_001_01', 'insp_001', 'hotspot', 'critical', 0.95,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.501,13.701]}'), 25.5, 75.5, 50.0, 'detected'),
('def_002', 'mod_001_02', 'insp_001', 'cell_anomaly', 'high', 0.88,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.502,13.701]}'), 15.2, 65.2, 50.0, 'reviewed'),
('def_003', 'mod_001_05', 'insp_001', 'delamination', 'medium', 0.76,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.501,13.702]}'), 8.5, 58.5, 50.0, 'detected'),
('def_004', 'mod_001_10', 'insp_001', 'soiling', 'low', 0.65,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.502,13.703]}'), 3.2, 53.2, 50.0, 'resolved'),
('def_005', 'mod_002_03', 'insp_002', 'hotspot', 'high', 0.91,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.523,13.721]}'), 18.7, 68.7, 50.0, 'detected'),
('def_006', 'mod_002_07', 'insp_002', 'diode_failure', 'critical', 0.97,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.524,13.722]}'), 22.3, 72.3, 50.0, 'detected'),
('def_007', 'mod_002_10', 'insp_002', 'crack', 'medium', 0.72,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.525,13.722]}'), 7.8, 57.8, 50.0, 'reviewed'),
('def_008', 'mod_003_02', 'insp_003', 'discoloration', 'low', 0.58,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.541,13.741]}'), 2.5, 52.5, 50.0, 'false_positive'),
('def_009', 'mod_003_05', 'insp_003', 'hotspot', 'medium', 0.81,
 ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.542,13.742]}'), 9.1, 59.1, 50.0, 'detected');

-- ==================== Thermal Images ====================
INSERT INTO thermal_images (id, inspection_id, module_id, image_path, s3_key, minio_bucket, capture_time, gps_location, altitude_m, processed, processed_at)
SELECT 
    'img_' || inspection_id || '_' || i,
    inspection_id,
    (SELECT id FROM modules WHERE site_id = i.site_id LIMIT 1),
    '/images/' || inspection_id || '/img_' || i || '.rjpeg',
    inspection_id || '/img_' || i || '.rjpeg',
    'thermal-images',
    started_at + (i * interval '1 minute'),
    ST_GeomFromGeoJSON('{"type":"Point","coordinates":[100.5,13.7]}'),
    50.0,
    true,
    NOW()
FROM inspections, generate_series(1, 5) AS i;

-- ==================== Reports ====================
INSERT INTO reports (id, site_id, inspection_id, report_type, format, s3_key, minio_bucket, status, generated_by) VALUES
('rpt_001', 'site_001', 'insp_001', 'inspection', 'pdf', 'reports/rpt_001.pdf', 'reports', 'completed', 'usr_admin_001'),
('rpt_002', 'site_002', 'insp_002', 'inspection', 'pdf', 'reports/rpt_002.pdf', 'reports', 'completed', 'usr_admin_001'),
('rpt_003', 'site_001', 'insp_001', 'summary', 'html', 'reports/rpt_003.html', 'reports', 'completed', 'usr_admin_001'),
('rpt_004', 'site_003', 'insp_003', 'compliance', 'pdf', 'reports/rpt_004.pdf', 'reports', 'generating', NULL);

-- ==================== Module Telemetry (TimescaleDB) ====================
-- Generate 30 days of telemetry data for each module
INSERT INTO module_telemetry (timestamp, module_id, temperature, power_output_w, voltage_v, current_a, efficiency, irradiance_w_m2, ambient_temperature)
SELECT 
    timestamp,
    module_id,
    -- Temperature varies with time of day and random factors
    25 + 15 * SIN(EXTRACT(HOUR FROM timestamp) / 24.0 * 2 * PI()) + (RANDOM() - 0.5) * 5 +
    CASE WHEN module_id LIKE '%001%' THEN 5 ELSE 0 END,  -- Some modules run hotter
    -- Power output based on irradiance and efficiency
    GREATEST(0, irradiance * 0.4 * (0.9 + (RANDOM() - 0.5) * 0.1)),
    -- Voltage
    38 + (RANDOM() - 0.5) * 2,
    -- Current
    GREATEST(0, irradiance * 0.01 * (0.9 + (RANDOM() - 0.5) * 0.1)),
    -- Efficiency degrades slightly over time
    0.92 - (EXTRACT(DAY FROM NOW() - timestamp) / 365.0 * 0.02) + (RANDOM() - 0.5) * 0.02,
    -- Irradiance follows sun pattern
    GREATEST(0, 800 * SIN(EXTRACT(HOUR FROM timestamp) / 24.0 * 2 * PI()) * 
    CASE WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 18 THEN 1 ELSE 0 END),
    -- Ambient temperature
    30 + 5 * SIN(EXTRACT(HOUR FROM timestamp) / 24.0 * 2 * PI()) + (RANDOM() - 0.5) * 3
FROM (
    SELECT 
        ts AS timestamp,
        m.id AS module_id
    FROM generate_series(
        NOW() - INTERVAL '30 days',
        NOW(),
        INTERVAL '1 hour'
    ) AS ts
    CROSS JOIN modules m
) AS data
WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 18;  -- Only daytime data

-- ==================== Update module counts ====================
UPDATE sites SET module_count = (
    SELECT COUNT(*) FROM modules WHERE site_id = sites.id
);

-- ==================== Audit Log Entries ====================
INSERT INTO audit_log (id, user_id, action, resource_type, resource_id, ip_address, metadata) VALUES
('audit_001', 'usr_admin_001', 'login', 'user', 'usr_admin_001', '192.168.1.100', '{"user_agent": "Mozilla/5.0"}'),
('audit_002', 'usr_admin_001', 'view_site', 'site', 'site_001', '192.168.1.100', '{}'),
('audit_003', 'usr_admin_001', 'generate_report', 'report', 'rpt_001', '192.168.1.100', '{"format": "pdf"}'),
('audit_004', NULL, 'system_startup', 'system', 'api-gateway', '127.0.0.1', '{"version": "1.0.0"}');

-- ==================== Verify Data ====================
SELECT 'Sites: ' || COUNT(*) FROM sites;
SELECT 'Modules: ' || COUNT(*) FROM modules;
SELECT 'Inspections: ' || COUNT(*) FROM inspections;
SELECT 'Defects: ' || COUNT(*) FROM defects;
SELECT 'Reports: ' || COUNT(*) FROM reports;
