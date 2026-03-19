// React Query Hooks for Data Fetching
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type {
  Site,
  Module,
  Defect,
  Inspection,
  Report,
  TelemetryPoint,
  DashboardStats,
} from '@/types';

// Query Keys
export const queryKeys = {
  sites: {
    all: ['sites'] as const,
    lists: () => [...queryKeys.sites.all, 'list'] as const,
    list: (filters: Record<string, string>) =>
      [...queryKeys.sites.lists(), filters] as const,
    details: () => [...queryKeys.sites.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.sites.details(), id] as const,
  },
  modules: {
    all: ['modules'] as const,
    lists: () => [...queryKeys.modules.all, 'list'] as const,
    list: (filters: Record<string, string>) =>
      [...queryKeys.modules.lists(), filters] as const,
    details: () => [...queryKeys.modules.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.modules.details(), id] as const,
    telemetry: (id: string) =>
      [...queryKeys.modules.detail(id), 'telemetry'] as const,
    defects: (id: string) =>
      [...queryKeys.modules.detail(id), 'defects'] as const,
  },
  defects: {
    all: ['defects'] as const,
    lists: () => [...queryKeys.defects.all, 'list'] as const,
    list: (filters: Record<string, string>) =>
      [...queryKeys.defects.lists(), filters] as const,
  },
  inspections: {
    all: ['inspections'] as const,
    lists: () => [...queryKeys.inspections.all, 'list'] as const,
    list: (filters: Record<string, string>) =>
      [...queryKeys.inspections.lists(), filters] as const,
    details: () => [...queryKeys.inspections.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.inspections.details(), id] as const,
  },
  reports: {
    all: ['reports'] as const,
    lists: () => [...queryKeys.reports.all, 'list'] as const,
    list: (filters: Record<string, string>) =>
      [...queryKeys.reports.lists(), filters] as const,
  },
  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
  },
};

// Sites Hooks
export function useSites(status?: string) {
  return useQuery({
    queryKey: queryKeys.sites.list(status ? { status } : {}),
    queryFn: () => apiClient.getSites(status),
  });
}

export function useSite(siteId: string) {
  return useQuery({
    queryKey: queryKeys.sites.detail(siteId),
    queryFn: () => apiClient.getSite(siteId),
    enabled: !!siteId,
  });
}

// Modules Hooks
export function useModule(moduleId: string) {
  return useQuery({
    queryKey: queryKeys.modules.detail(moduleId),
    queryFn: () => apiClient.getModule(moduleId),
    enabled: !!moduleId,
  });
}

export function useModuleTelemetry(moduleId: string, days: number = 30) {
  return useQuery({
    queryKey: queryKeys.modules.telemetry(moduleId),
    queryFn: () => apiClient.getModuleTelemetry(moduleId, days),
    enabled: !!moduleId,
  });
}

export function useModuleDefects(moduleId: string) {
  return useQuery({
    queryKey: queryKeys.modules.defects(moduleId),
    queryFn: () => apiClient.getModuleDefects(moduleId),
    enabled: !!moduleId,
  });
}

// Defects Hooks
export function useDefects(filters?: {
  site_id?: string;
  module_id?: string;
  severity?: string;
}) {
  return useQuery({
    queryKey: queryKeys.defects.list(filters || {}),
    queryFn: () => apiClient.getDefects(filters),
  });
}

export function useCriticalDefects() {
  return useQuery({
    queryKey: queryKeys.defects.list({ severity: 'critical' }),
    queryFn: () => apiClient.getDefects({ severity: 'critical' }),
  });
}

// Inspections Hooks
export function useInspections(siteId?: string) {
  return useQuery({
    queryKey: queryKeys.inspections.list(siteId ? { site_id: siteId } : {}),
    queryFn: () => apiClient.getInspections(siteId),
  });
}

export function useInspection(inspectionId: string) {
  return useQuery({
    queryKey: queryKeys.inspections.detail(inspectionId),
    queryFn: () => apiClient.getInspection(inspectionId),
    enabled: !!inspectionId,
  });
}

// Reports Hooks
export function useReports(siteId?: string) {
  return useQuery({
    queryKey: queryKeys.reports.list(siteId ? { site_id: siteId } : {}),
    queryFn: () => apiClient.getReports(siteId),
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      siteId,
      inspectionId,
      format,
    }: {
      siteId: string;
      inspectionId: string;
      format?: string;
    }) => apiClient.generateReport(siteId, inspectionId, format),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reports.all });
    },
  });
}

// Dashboard Hook
export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboard.stats(),
    queryFn: () => apiClient.getDashboardStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 1, // Only retry once
    staleTime: 5000, // Consider data fresh for 5 seconds
    placeholderData: (previousData) => previousData, // Keep previous data while loading
  });
}
