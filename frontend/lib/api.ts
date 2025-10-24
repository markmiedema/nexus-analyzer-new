/**
 * API client utilities and endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/v1`;

// Types
export interface Analysis {
  analysis_id: string;
  business_profile_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfile {
  profile_id: string;
  analysis_id: string;
  legal_business_name: string;
  doing_business_as?: string;
  federal_ein?: string;
  business_structure?: string;
  industry?: string;
  naics_code?: string;
  has_physical_presence: boolean;
  has_employees: boolean;
  has_inventory: boolean;
  uses_marketplace_facilitators: boolean;
  marketplace_facilitator_names?: string[];
  sells_tangible_goods: boolean;
  sells_digital_goods: boolean;
  sells_services: boolean;
  has_exempt_sales: boolean;
  exempt_customer_types?: string[];
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface NexusResult {
  result_id: string;
  analysis_id: string;
  state: string;
  has_physical_nexus: boolean;
  has_economic_nexus: boolean;
  nexus_status: string;
  total_sales: number;
  total_transactions: number;
  created_at: string;
}

export interface LiabilityEstimate {
  estimate_id: string;
  analysis_id: string;
  state: string;
  estimated_liability: number;
  filing_frequency?: string;
  created_at: string;
}

export interface Report {
  report_id: string;
  analysis_id: string;
  report_type: string;
  file_path: string;
  created_at: string;
}

// Helper function to handle API errors
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object' && 'detail' in error) {
    return String(error.detail);
  }
  return 'An unexpected error occurred';
}

// Generic fetch wrapper with auth
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Send httpOnly cookies with requests
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
  }

  return response.json();
}

// Analyses API
export const analysesApi = {
  list: async (): Promise<Analysis[]> => {
    return apiFetch<Analysis[]>('/analyses');
  },

  get: async (id: string): Promise<Analysis> => {
    return apiFetch<Analysis>(`/analyses/${id}`);
  },

  create: async (data: { client_name: string; period_start: string; period_end: string }): Promise<Analysis> => {
    return apiFetch<Analysis>('/analyses', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/analyses/${id}`, {
      method: 'DELETE',
    });
  },

  uploadCSV: async (analysisId: string, file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/analyses/${analysisId}/upload`, {
      method: 'POST',
      credentials: 'include', // Send httpOnly cookies
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Upload failed');
    }

    return response.json();
  },
};

// Business Profile API
export const businessProfileApi = {
  list: async (): Promise<BusinessProfile[]> => {
    return apiFetch<BusinessProfile[]>('/business-profile');
  },

  get: async (id: string): Promise<BusinessProfile> => {
    return apiFetch<BusinessProfile>(`/business-profile/${id}`);
  },

  create: async (data: Partial<BusinessProfile>): Promise<BusinessProfile> => {
    return apiFetch<BusinessProfile>('/business-profile', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (
    id: string,
    data: Partial<BusinessProfile>
  ): Promise<BusinessProfile> => {
    return apiFetch<BusinessProfile>(`/business-profile/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/business-profile/${id}`, {
      method: 'DELETE',
    });
  },
};

// Nexus API
export const nexusApi = {
  getResults: async (analysisId: string): Promise<NexusResult[]> => {
    return apiFetch<NexusResult[]>(`/nexus/results/${analysisId}`);
  },

  getResultByState: async (
    analysisId: string,
    state: string
  ): Promise<NexusResult> => {
    return apiFetch<NexusResult>(`/nexus/results/${analysisId}/${state}`);
  },
};

// Liability API
export const liabilityApi = {
  getEstimates: async (analysisId: string): Promise<LiabilityEstimate[]> => {
    return apiFetch<LiabilityEstimate[]>(`/liability/estimates/${analysisId}`);
  },

  calculateEstimate: async (
    analysisId: string,
    state: string
  ): Promise<LiabilityEstimate> => {
    return apiFetch<LiabilityEstimate>(
      `/liability/calculate/${analysisId}/${state}`,
      {
        method: 'POST',
      }
    );
  },
};

// Reports API
export const reportsApi = {
  list: async (analysisId: string): Promise<Report[]> => {
    return apiFetch<Report[]>(`/reports/list/${analysisId}`);
  },

  generate: async (
    analysisId: string,
    reportType: 'summary' | 'detailed' | 'compliance'
  ): Promise<Report> => {
    return apiFetch<Report>(`/reports/generate/${analysisId}`, {
      method: 'POST',
      body: JSON.stringify({
        report_type: reportType,
      }),
    });
  },

  download: async (reportId: string): Promise<Blob> => {
    const response = await fetch(`${API_URL}/reports/${reportId}/download`, {
      credentials: 'include', // Send httpOnly cookies
    });

    if (!response.ok) {
      throw new Error('Failed to download report');
    }

    return response.blob();
  },
};

const api = {
  analysesApi,
  businessProfileApi,
  nexusApi,
  liabilityApi,
  reportsApi,
  getErrorMessage,
};

export default api;
