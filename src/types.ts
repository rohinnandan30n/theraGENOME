// TypeScript type definitions for Variant Results API

export interface VariantResult {
  result_id: string; // UUID
  patient_id: string; // UUID - FK to patients table
  variant_id?: string;
  chrom?: string;
  pos?: number;
  ref?: string;
  alt?: string;
  prediction: "Pathogenic" | "Benign" | "VUS";
  confidence: number; // 0-1
  probabilities?: Record<string, number>; // JSONB
  model_version?: string; // v1, v2, v3
  feature_importance?: Record<string, unknown>; // JSONB
  clinical_notes?: string;
  created_by?: string; // UUID
  created_at?: string; // ISO timestamp
  updated_at?: string; // ISO timestamp
  deleted_at?: string | null; // ISO timestamp
  is_deleted?: boolean;
  metadata?: Record<string, unknown>; // JSONB
}

export interface VariantAuditLog {
  audit_id: string; // UUID
  result_id: string; // UUID
  patient_id: string; // UUID
  operation: "INSERT" | "UPDATE" | "DELETE";
  old_data?: Record<string, unknown>; // JSONB
  new_data?: Record<string, unknown>; // JSONB
  changed_fields?: string[]; // TEXT[]
  changed_by?: string; // UUID
  changed_at?: string; // ISO timestamp
  ip_address?: string;
  user_agent?: string;
  metadata?: Record<string, unknown>; // JSONB
}

export interface ListVariantResultsQuery {
  limit?: number; // 1-100, default 20
  offset?: number; // default 0
  start_date?: string; // ISO format
  end_date?: string; // ISO format
  prediction?: "Pathogenic" | "Benign" | "VUS";
  model_version?: string;
  include_deleted?: boolean; // default false
  sort_by?: "created_at" | "confidence" | "prediction";
  sort_order?: "ASC" | "DESC"; // default DESC
}

export interface CreateVariantResultRequest {
  variant_id?: string;
  chrom?: string;
  pos?: number;
  ref?: string;
  alt?: string;
  prediction: "Pathogenic" | "Benign" | "VUS";
  confidence: number;
  probabilities?: Record<string, number>;
  model_version?: string;
  feature_importance?: Record<string, unknown>;
  clinical_notes?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateVariantResultRequest {
  prediction?: "Pathogenic" | "Benign" | "VUS";
  clinical_notes?: string;
  metadata?: Record<string, unknown>;
}

export interface ListResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface PaginationParams {
  limit: number;
  offset: number;
}

export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
}

export interface StatisticsResponse {
  statistics: {
    total: number;
    pathogenic_count: number;
    benign_count: number;
    vus_count: number;
    avg_confidence: number;
    last_result_date: string | null;
  };
}
