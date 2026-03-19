// API Types for Doctor Doom System

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'operator' | 'admin' | 'super_admin';
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Site {
  id: string;
  name: string;
  location: GeoJSONPolygon;
  area_hectares: number;
  module_count: number;
  address?: string;
  city?: string;
  country?: string;
  status: 'active' | 'inactive' | 'maintenance';
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Module {
  id: string;
  site_id: string;
  position: GeoJSONPoint;
  orientation: number;
  tilt: number;
  rated_power_w: number;
  cell_count: number;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  installed_at?: string;
  status: 'active' | 'inactive' | 'maintenance';
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Defect {
  id: string;
  module_id: string;
  inspection_id?: string;
  defect_type: DefectType;
  severity: Severity;
  confidence: number;
  location?: GeoJSONPoint;
  bounding_box?: [number, number, number, number];
  temperature_delta: number;
  max_temperature?: number;
  ambient_temperature?: number;
  ml_model_version?: string;
  status: 'detected' | 'reviewed' | 'resolved' | 'false_positive';
  reviewer_id?: string;
  reviewed_at?: string;
  notes?: string;
  metadata: Record<string, unknown>;
  detected_at: string;
  created_at: string;
}

export type DefectType =
  | 'hotspot'
  | 'cell_anomaly'
  | 'delamination'
  | 'diode_failure'
  | 'soiling'
  | 'crack'
  | 'discoloration'
  | 'other';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface Inspection {
  id: string;
  site_id: string;
  drone_id: string;
  pilot_id?: string;
  started_at: string;
  completed_at?: string;
  image_count: number;
  flight_path?: GeoJSONLineString;
  weather_conditions?: Record<string, unknown>;
  status: 'in_progress' | 'completed' | 'failed';
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ThermalImage {
  id: string;
  inspection_id: string;
  module_id?: string;
  image_path: string;
  s3_key?: string;
  minio_bucket: string;
  capture_time: string;
  gps_location?: GeoJSONPoint;
  altitude_m?: number;
  camera_angle?: number;
  thermal_metadata: ThermalMetadata;
  processed: boolean;
  processed_at?: string;
  created_at: string;
}

export interface ThermalMetadata {
  width: number;
  height: number;
  temperature_range: {
    min: number;
    max: number;
  };
  emissivity: number;
  reflected_temp: number;
  atmospheric_temp: number;
  distance: number;
  relative_humidity: number;
}

export interface Report {
  id: string;
  site_id: string;
  inspection_id?: string;
  report_type: 'inspection' | 'summary' | 'compliance';
  format: 'pdf' | 'html' | 'json';
  s3_key?: string;
  minio_bucket: string;
  file_size_bytes?: number;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  generated_by?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
}

export interface TelemetryPoint {
  timestamp: string;
  module_id: string;
  temperature: number;
  power_output_w: number;
  voltage_v?: number;
  current_a?: number;
  efficiency: number;
  irradiance_w_m2?: number;
  ambient_temperature?: number;
  wind_speed_m_s?: number;
}

export interface DashboardStats {
  total_sites: number;
  total_modules: number;
  total_defects: number;
  critical_defects: number;
  inspections_this_month: number;
  average_health_score: number;
  recent_alerts: Alert[];
}

export interface Alert {
  id: string;
  type: 'defect' | 'inspection' | 'system';
  severity: Severity;
  title: string;
  message: string;
  created_at: string;
  read: boolean;
}

// GeoJSON types
export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number];
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: number[][];
}

// API Response types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Flight planning
export interface FlightPlan {
  id: string;
  site_id: string;
  name: string;
  waypoints: Waypoint[];
  altitude_m: number;
  speed_m_s: number;
  overlap_percent: number;
  sidelap_percent: number;
  status: 'draft' | 'ready' | 'in_progress' | 'completed';
  created_at: string;
}

export interface Waypoint {
  id: string;
  latitude: number;
  longitude: number;
  altitude_m: number;
  action?: string;
}

// Health score
export interface HealthScore {
  module_id: string;
  score: number; // 0-100
  factors: HealthFactor[];
  calculated_at: string;
}

export interface HealthFactor {
  name: string;
  impact: number;
  description: string;
}
