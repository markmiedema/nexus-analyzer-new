import axios, { AxiosError } from 'axios';
import type {
  Analysis,
  BusinessProfile,
  NexusResult,
  LiabilityEstimate,
  Report,
  ErrorResponse,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;
    if (axiosError.response?.data?.detail) {
      const detail = axiosError.response.data.detail;
      if (typeof detail === 'string') {
        return detail;
      } else if (Array.isArray(detail)) {
        return detail.map((err) => err.msg).join(', ');
      }
    }
    return axiosError.message;
  }
  return 'An unknown error occurred';
}

// Business Profile API
export const businessProfileApi = {
  list: () => apiClient.get<BusinessProfile[]>('/api/v1/business-profiles'),
  get: (id: string) => apiClient.get<BusinessProfile>(`/api/v1/business-profiles/${id}`),
  create: (data: Partial<BusinessProfile>) => apiClient.post<BusinessProfile>('/api/v1/business-profiles', data),
};

// Analyses API
export const analysesApi = {
  list: () => apiClient.get<Analysis[]>('/api/v1/analyses'),
  get: (id: string) => apiClient.get<Analysis>(`/api/v1/analyses/${id}`),
  create: (businessProfileId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('business_profile_id', businessProfileId);
    return apiClient.post<Analysis>('/api/v1/analyses', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  delete: (id: string) => apiClient.delete(`/api/v1/analyses/${id}`),
};

// Nexus API
export const nexusApi = {
  getResults: (analysisId: string) => apiClient.get<NexusResult[]>(`/api/v1/nexus/results/${analysisId}`),
  getRules: () => apiClient.get('/api/v1/nexus/rules'),
};

// Liability API
export const liabilityApi = {
  getEstimates: (analysisId: string) => apiClient.get<LiabilityEstimate[]>(`/api/v1/liability/estimates/${analysisId}`),
};

// Reports API
export const reportsApi = {
  list: (analysisId: string) => apiClient.get<Report[]>(`/api/v1/reports/${analysisId}`),
  generate: (analysisId: string, reportType: string) =>
    apiClient.post<Report>(`/api/v1/reports/generate`, {
      analysis_id: analysisId,
      report_type: reportType,
    }),
  download: (reportId: string) => apiClient.get(`/api/v1/reports/download/${reportId}`, { responseType: 'blob' }),
};

export type { Analysis, BusinessProfile, NexusResult, LiabilityEstimate, Report };
