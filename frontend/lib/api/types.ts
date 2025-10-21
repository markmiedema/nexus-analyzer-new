// API Types

export enum AnalysisStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Analysis {
  analysis_id: string;
  business_profile_id: string;
  status: AnalysisStatus;
  file_name: string;
  file_size: number;
  total_transactions: number | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfile {
  profile_id: string;
  business_name: string;
  ein: string;
  created_at: string;
}

export interface NexusResult {
  result_id: string;
  analysis_id: string;
  state_code: string;
  state_name: string;
  has_nexus: boolean;
  total_sales: number;
  total_transactions: number;
  threshold_sales: number | null;
  threshold_transactions: number | null;
  created_at: string;
}

export interface LiabilityEstimate {
  estimate_id: string;
  result_id: string;
  state_code: string;
  estimated_liability: number;
  state_tax_rate: number;
  avg_local_tax_rate: number;
  interest_amount: number;
  penalty_amount: number;
  total_amount_due: number;
  created_at: string;
}

export interface Report {
  report_id: string;
  analysis_id: string;
  report_type: string;
  file_path: string;
  generated_at: string;
}

export interface ErrorResponse {
  detail: string | { msg: string; type: string }[];
}
