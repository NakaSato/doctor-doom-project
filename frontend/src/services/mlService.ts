/**
 * ML Service Integration
 * 
 * Connects frontend to ML Inference Service
 */

const ML_SERVICE_URL = import.meta.env.VITE_ML_SERVICE_URL || 'http://localhost:8001';

export interface MLAnalysisRequest {
  module_id: string;
  inspection_id: string;
  image_id: string;
  thermal_data?: string;
  metadata?: {
    drone_model?: string;
    camera_model?: string;
    altitude?: number;
    irradiance?: number;
    ambient_temp?: number;
    [key: string]: any;
  };
}

export interface MLDefect {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  severity_score: number;
  confidence: number;
  temperature_delta: number;
  max_temperature: number;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  recommendations: Array<{
    priority: number;
    action: string;
    description: string;
    estimated_power_loss?: string;
    safety_risk?: string;
  }>;
}

export interface MLAnalysisResult {
  module_id: string;
  inspection_id: string;
  image_id: string;
  defect_type: string;
  severity: string;
  severity_score: number;
  confidence: number;
  temperature_delta: number;
  max_temperature: number;
  processing_time_ms: number;
  timestamp: string;
  defects: MLDefect[];
  recommendations: Array<{
    priority: number;
    action: string;
    description: string;
    estimated_power_loss?: string;
    safety_risk?: string;
  }>;
}

export interface MLPipelineInfo {
  stages: Array<{
    id: number;
    name: string;
    model: string;
    description: string;
  }>;
  total_latency_ms: number;
  supported_defect_types: string[];
  severity_levels: string[];
}

/**
 * Check ML service health
 */
export async function checkMLServiceHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('ML service health check failed:', error);
    return false;
  }
}

/**
 * Get ML pipeline information
 */
export async function getPipelineInfo(): Promise<MLPipelineInfo> {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/ml/stages`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  } catch (error) {
    console.error('Failed to fetch pipeline info:', error);
    throw error;
  }
}

/**
 * Analyze a single module with ML service
 */
export async function analyzeModule(
  request: MLAnalysisRequest
): Promise<MLAnalysisResult> {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/ml/infer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Analysis failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('ML analysis failed:', error);
    throw error;
  }
}

/**
 * Analyze multiple modules in batch
 */
export async function analyzeBatch(
  requests: MLAnalysisRequest[],
  max_batch_size: number = 8
): Promise<{ results: MLAnalysisResult[] }> {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/ml/infer/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ requests, max_batch_size }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Batch analysis failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Batch ML analysis failed:', error);
    throw error;
  }
}

/**
 * Convert ML result to frontend format
 */
export function convertMLResultToFrontendFormat(mlResult: MLAnalysisResult) {
  return {
    id: mlResult.image_id,
    module_id: mlResult.module_id,
    defect_type: mlResult.defect_type,
    severity: mlResult.severity as 'critical' | 'major' | 'minor' | 'low',
    confidence: mlResult.confidence,
    deltaT: mlResult.temperature_delta,
    maxTemp: mlResult.max_temperature,
    timestamp: mlResult.timestamp,
    defects: mlResult.defects.map(d => ({
      id: `${mlResult.image_id}_${d.type}`,
      type: d.type,
      severity: d.severity,
      deltaT: d.temperature_delta,
      confidence: d.confidence,
      x: d.bounding_box?.x || 0.5,
      y: d.bounding_box?.y || 0.5,
      width: d.bounding_box?.width || 0.1,
      height: d.bounding_box?.height || 0.1,
    })),
    recommendations: mlResult.recommendations,
  };
}

/**
 * Start ML service (for development)
 * Opens ML service in new window/tab if not running
 */
export function openMLServiceDashboard() {
  window.open(ML_SERVICE_URL, '_blank');
}

/**
 * Get ML service status
 */
export async function getMLServiceStatus(): Promise<{
  running: boolean;
  url: string;
  pipeline?: MLPipelineInfo;
}> {
  const running = await checkMLServiceHealth();
  const pipeline = running ? await getPipelineInfo().catch(() => undefined) : undefined;
  
  return {
    running,
    url: ML_SERVICE_URL,
    pipeline,
  };
}
