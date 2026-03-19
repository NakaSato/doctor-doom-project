/**
 * ML Inference React Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  analyzeModule,
  analyzeBatch,
  getPipelineInfo,
  getDefectTypes,
  getSeverityLevels,
  checkMLHealth,
  type AnalysisRequest,
  type BatchAnalysisRequest,
} from '@/services/ml';
import type {
  AnalysisResult,
  BatchAnalysisResult,
  PipelineInfo,
  DefectTypeInfo,
  SeverityLevelInfo,
  MLHealthStatus,
} from '@/types/ml';

// Query keys
export const mlKeys = {
  all: ['ml'] as const,
  health: () => [...mlKeys.all, 'health'] as const,
  pipeline: () => [...mlKeys.all, 'pipeline'] as const,
  defectTypes: () => [...mlKeys.all, 'defectTypes'] as const,
  severityLevels: () => [...mlKeys.all, 'severityLevels'] as const,
  analysis: (moduleId?: string) => [...mlKeys.all, 'analysis', moduleId] as const,
  batchAnalysis: () => [...mlKeys.all, 'batchAnalysis'] as const,
};

/**
 * Hook: Analyze single thermal image
 */
export function useAnalyzeModule() {
  const queryClient = useQueryClient();

  return useMutation<AnalysisResult, Error, AnalysisRequest>({
    mutationFn: analyzeModule,
    onSuccess: (data) => {
      // Invalidate analysis cache for this module
      queryClient.invalidateQueries({ queryKey: mlKeys.analysis(data.module_id) });
    },
    retry: 1,
    meta: {
      errorMessage: 'Failed to analyze thermal image',
    },
  });
}

/**
 * Hook: Analyze batch of thermal images
 */
export function useAnalyzeBatch() {
  const queryClient = useQueryClient();

  return useMutation<BatchAnalysisResult, Error, BatchAnalysisRequest>({
    mutationFn: analyzeBatch,
    onSuccess: (data) => {
      // Invalidate analysis cache for all modules in batch
      data.results.forEach((result) => {
        queryClient.invalidateQueries({ queryKey: mlKeys.analysis(result.module_id) });
      });
    },
    retry: 1,
    meta: {
      errorMessage: 'Failed to analyze batch of images',
    },
  });
}

/**
 * Hook: Get ML pipeline info
 */
export function usePipelineInfo() {
  return useQuery<PipelineInfo, Error>({
    queryKey: mlKeys.pipeline(),
    queryFn: getPipelineInfo,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook: Get defect types
 */
export function useDefectTypes() {
  return useQuery<DefectTypeInfo[], Error>({
    queryKey: mlKeys.defectTypes(),
    queryFn: getDefectTypes,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
}

/**
 * Hook: Get severity levels
 */
export function useSeverityLevels() {
  return useQuery<SeverityLevelInfo[], Error>({
    queryKey: mlKeys.severityLevels(),
    queryFn: getSeverityLevels,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
}

/**
 * Hook: Check ML service health
 */
export function useMLHealth(refreshInterval?: number) {
  return useQuery<MLHealthStatus, Error>({
    queryKey: mlKeys.health(),
    queryFn: checkMLHealth,
    refetchInterval: refreshInterval || 30000, // 30 seconds
    retry: 3,
  });
}

/**
 * Hook: Get cached analysis result for a module
 */
export function useModuleAnalysis(moduleId: string) {
  const queryClient = useQueryClient();
  return queryClient.getQueryData<AnalysisResult>(mlKeys.analysis(moduleId));
}
