/**
 * ML Inference API Client
 * 
 * Interfaces with the ML Inference Service for thermal image analysis.
 */

import type {
  DefectType,
  SeverityLevel,
  AnalysisRequest,
  AnalysisResult,
  BatchAnalysisRequest,
  BatchAnalysisResult,
  PipelineInfo,
  DefectTypeInfo,
  SeverityLevelInfo,
} from '@/types/ml';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Analyze a single thermal image for defects
 */
export async function analyzeModule(
  request: AnalysisRequest
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/ml/infer`, {
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
}

/**
 * Analyze multiple thermal images in batch
 */
export async function analyzeBatch(
  request: BatchAnalysisRequest
): Promise<BatchAnalysisResult> {
  const response = await fetch(`${API_BASE}/ml/infer/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Batch analysis failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get ML pipeline information
 */
export async function getPipelineInfo(): Promise<PipelineInfo> {
  const response = await fetch(`${API_BASE}/ml/stages`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch pipeline info: ${response.status}`);
  }

  return response.json();
}

/**
 * Get supported defect types
 */
export async function getDefectTypes(): Promise<DefectTypeInfo[]> {
  const response = await fetch(`${API_BASE}/ml/defect-types`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch defect types: ${response.status}`);
  }

  const data = await response.json();
  return data.defect_types || [];
}

/**
 * Get severity levels
 */
export async function getSeverityLevels(): Promise<SeverityLevelInfo[]> {
  const response = await fetch(`${API_BASE}/ml/severity-levels`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch severity levels: ${response.status}`);
  }

  const data = await response.json();
  return data.severity_levels || [];
}

/**
 * Check ML service health
 */
export async function checkMLHealth(): Promise<{
  status: string;
  service: string;
  version: string;
  models_loaded: boolean;
}> {
  const response = await fetch(`${API_BASE.replace('/api/v1', '')}/health`);
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Convert image file to base64 for API submission
 */
export function imageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data:image/jpeg;base64, prefix
      const base64 = result.split(',')[1] || result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Convert thermal data array to base64
 */
export function thermalDataToBase64(thermalData: Float32Array): string {
  const bytes = new Uint8Array(thermalData.buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
