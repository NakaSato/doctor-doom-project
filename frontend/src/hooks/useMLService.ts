/**
 * React Query Hooks for ML Service
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  checkMLServiceHealth,
  getPipelineInfo,
  analyzeModule,
  analyzeBatch,
  getMLServiceStatus,
  type MLAnalysisRequest,
  type MLAnalysisResult,
} from '@/services/mlService';

/**
 * Hook to check ML service health
 */
export function useMLServiceHealth(refreshInterval?: number) {
  return useQuery({
    queryKey: ['ml-service', 'health'],
    queryFn: checkMLServiceHealth,
    refetchInterval: refreshInterval || 30000, // 30 seconds
    retry: 3,
    staleTime: 5000,
  });
}

/**
 * Hook to get ML pipeline information
 */
export function useMLPipeline() {
  return useQuery({
    queryKey: ['ml-service', 'pipeline'],
    queryFn: getPipelineInfo,
    staleTime: 60000, // 1 minute
    retry: 2,
  });
}

/**
 * Hook to get ML service status (health + pipeline)
 */
export function useMLServiceStatus() {
  return useQuery({
    queryKey: ['ml-service', 'status'],
    queryFn: getMLServiceStatus,
    staleTime: 10000, // 10 seconds
    retry: 1,
  });
}

/**
 * Hook to analyze a single module
 */
export function useModuleAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: MLAnalysisRequest) => analyzeModule(request),
    onSuccess: (data: MLAnalysisResult) => {
      // Invalidate health check to refresh status
      queryClient.invalidateQueries({ queryKey: ['ml-service', 'health'] });
      
      // Cache the result
      queryClient.setQueryData(
        ['ml-analysis', data.module_id, data.image_id],
        data
      );
    },
    retry: 1,
  });
}

/**
 * Hook to analyze multiple modules in batch
 */
export function useBatchAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ requests, max_batch_size }: { requests: MLAnalysisRequest[], max_batch_size?: number }) =>
      analyzeBatch(requests, max_batch_size),
    onSuccess: (data) => {
      // Invalidate health check
      queryClient.invalidateQueries({ queryKey: ['ml-service', 'health'] });
      
      // Cache all results
      data.results.forEach(result => {
        queryClient.setQueryData(
          ['ml-analysis', result.module_id, result.image_id],
          result
        );
      });
    },
    retry: 1,
  });
}

/**
 * Hook to analyze entire array with progress tracking
 */
export function useArrayAnalysis() {
  const queryClient = useQueryClient();
  const batchMutation = useBatchAnalysis();

  const analyzeArray = async (
    requests: MLAnalysisRequest[],
    onProgress?: (progress: number, current: number, total: number) => void
  ) => {
    const total = requests.length;
    const batchSize = 8;
    const batches = Math.ceil(total / batchSize);
    
    const allResults: MLAnalysisResult[] = [];
    
    for (let i = 0; i < batches; i++) {
      const batch = requests.slice(i * batchSize, (i + 1) * batchSize);
      const result = await batchMutation.mutateAsync({
        requests: batch,
        max_batch_size: batchSize,
      });
      
      allResults.push(...result.results);
      
      if (onProgress) {
        onProgress(Math.min(((i + 1) * batchSize / total) * 100, 100), (i + 1) * batchSize, total);
      }
    }
    
    return { results: allResults };
  };

  return {
    analyzeArray,
    isLoading: batchMutation.isPending,
    error: batchMutation.error,
    reset: batchMutation.reset,
  };
}
