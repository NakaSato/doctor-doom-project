/**
 * ML Inference Types
 */

export type DefectType =
  | 'hotspot'
  | 'cell_anomaly'
  | 'delamination'
  | 'diode_failure'
  | 'crack'
  | 'soiling'
  | 'discoloration'
  | 'snail_track'
  | 'burn_mark'
  | 'corrosion'
  | 'potential_induced'
  | 'broken_cell'
  | 'normal';

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface AnalysisRequest {
  module_id: string;
  inspection_id: string;
  image_id: string;
  thermal_data: string; // Base64 encoded
  metadata?: {
    ambient_temp?: number;
    irradiance?: number;
    neighbor_temps?: number[];
    string_mean?: number;
    array_mean?: number;
    expected_temp?: number;
    string_position?: number;
    row_index?: number;
    col_index?: number;
    time_of_day?: number;
    wind_speed?: number;
    humidity?: number;
  };
}

export interface AnalysisResult {
  module_id: string;
  inspection_id: string;
  image_id: string;
  defect_type: DefectType;
  severity: SeverityLevel;
  severity_score: number;
  confidence: number;
  temperature_delta: number;
  max_temperature: number;
  ambient_temperature: number;
  affected_cells: number[];
  recommendations: Recommendation[];
  anomaly_score?: number;
  processing_time_ms: number;
  model_version: string;
  timestamp: string;
}

export interface Recommendation {
  priority: number;
  action: string;
  description: string;
  estimated_power_loss?: string;
  safety_risk?: string;
}

export interface BatchAnalysisRequest {
  requests: AnalysisRequest[];
  max_batch_size?: number;
}

export interface BatchAnalysisResult {
  results: AnalysisResult[];
  count: number;
  total_processing_time_ms: number;
  avg_time_per_image_ms: number;
}

export interface PipelineStage {
  id: number;
  name: string;
  description: string;
  architecture: string;
  input: {
    shape?: number[];
    type: string;
  };
  output: {
    shape?: number[];
    type: string;
    classes?: string[];
  };
  latency_ms: number;
  model_size_mb: number;
  accuracy?: number;
}

export interface PipelineInfo {
  stages: PipelineStage[];
  total_latency_ms: number;
  total_model_size_mb: number;
}

export interface DefectTypeInfo {
  id: number;
  name: DefectType;
  description: string;
  thermal_pattern: string;
  severity_range: string;
  frequency?: string;
}

export interface SeverityLevelInfo {
  level: SeverityLevel;
  score_range: [number, number];
  action: string;
  timeline: string;
  color: string;
}

export interface MLHealthStatus {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  models_loaded: boolean;
  stages?: number;
}
