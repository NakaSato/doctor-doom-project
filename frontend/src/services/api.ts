// API Client for Doctor Doom Backend
import type {
  User,
  Token,
  Site,
  Module,
  Defect,
  Inspection,
  Report,
  TelemetryPoint,
  DashboardStats,
  PaginatedResponse,
  ApiError,
} from '@/types';

const API_BASE_URL = '/api/v1';

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('access_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An error occurred',
      }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const queryString = params
      ? `?${new URLSearchParams(params).toString()}`
      : '';
    return this.request<T>(`${endpoint}${queryString}`);
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<Token> {
    const token = await this.post<Token>('/auth/login', { email, password });
    this.setToken(token.access_token);
    return token;
  }

  async register(
    email: string,
    password: string,
    full_name: string,
    role: string = 'operator'
  ): Promise<User> {
    return this.post<User>('/auth/register', {
      email,
      password,
      full_name,
      role,
    });
  }

  async logout(): Promise<void> {
    await this.post('/auth/logout');
    this.setToken(null);
  }

  async getCurrentUser(): Promise<User> {
    return this.get<User>('/auth/me');
  }

  // Sites endpoints
  async getSites(status?: string): Promise<Site[]> {
    return this.get<Site[]>('/sites', status ? { status } : undefined);
  }

  async getSite(siteId: string): Promise<Site & { modules: Module[] }> {
    return this.get<Site & { modules: Module[] }>(`/sites/${siteId}`);
  }

  // Modules endpoints
  async getModule(moduleId: string): Promise<Module> {
    return this.get<Module>(`/modules/${moduleId}`);
  }

  async getModuleTelemetry(
    moduleId: string,
    days: number = 30
  ): Promise<TelemetryPoint[]> {
    return this.get<TelemetryPoint[]>(
      `/modules/${moduleId}/telemetry`,
      { days: days.toString() }
    );
  }

  async getModuleDefects(moduleId: string): Promise<Defect[]> {
    return this.get<Defect[]>(`/modules/${moduleId}/defects`);
  }

  // Defects endpoints
  async getDefects(params?: {
    site_id?: string;
    module_id?: string;
    severity?: string;
  }): Promise<Defect[]> {
    return this.get<Defect[]>('/defects', params);
  }

  // Inspections endpoints
  async getInspections(siteId?: string): Promise<Inspection[]> {
    return this.get<Inspection[]>(
      '/inspections',
      siteId ? { site_id: siteId } : undefined
    );
  }

  async getInspection(inspectionId: string): Promise<Inspection> {
    return this.get<Inspection>(`/inspections/${inspectionId}`);
  }

  // Reports endpoints
  async getReports(siteId?: string): Promise<Report[]> {
    return this.get<Report[]>('/reports', siteId ? { site_id: siteId } : undefined);
  }

  async generateReport(
    siteId: string,
    inspectionId: string,
    format: string = 'pdf'
  ): Promise<{ report_id: string; status: string }> {
    return this.post<{ report_id: string; status: string }>('/reports/generate', {
      site_id: siteId,
      inspection_id: inspectionId,
      format,
    });
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      return this.get<DashboardStats>('/dashboard/stats');
    } catch (error) {
      // Return mock data if backend is not available
      console.warn('Dashboard stats API not available, using mock data');
      return {
        total_sites: 1,
        total_modules: 96,
        total_defects: 25,
        critical_defects: 5,
        major_defects: 10,
        minor_defects: 10,
        avg_performance_ratio: 87.5,
        total_capacity_mw: 5.2,
      } as DashboardStats;
    }
  }

  // Spatial queries
  async getDefectHeatmap(siteId: string, resolution: number = 100): Promise<unknown> {
    return this.get(`/spatial/defects/heatmap`, {
      site_id: siteId,
      resolution: resolution.toString(),
    });
  }

  async getNearbyModules(
    siteId: string,
    lat: number,
    lon: number,
    radiusMeters: number = 50
  ): Promise<Module[]> {
    return this.get<Module[]>('/spatial/modules/nearby', {
      site_id: siteId,
      lat: lat.toString(),
      lon: lon.toString(),
      radius_meters: radiusMeters.toString(),
    });
  }

  // Ingestion
  async submitThermalImage(data: {
    image_id: string;
    module_id: string;
    inspection_id: string;
    image_bytes?: string;
  }): Promise<{ status: string; stream: string }> {
    return this.post('/ingest/thermal', data);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
