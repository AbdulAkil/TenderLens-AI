export type Tender = {
  id: string;
  source_id: string;
  source_url: string;
  title: string;
  description: string | null;
  buyer_name: string | null;
  country_code: string | null;
  region_code: string | null;
  publication_date: string | null;
  submission_deadline: string | null;
  estimated_value: string | null;
  currency: string | null;
  procedure_type: string | null;
  cpv_code_values: string[];
};

export type TenderPage = { items: Tender[]; total: number; limit: number; offset: number };

export type Company = {
  id: string;
  name: string;
  description: string | null;
  services: string[];
  industries: string[];
  skills: string[];
  certifications: string[];
  preferred_locations: string[];
  cpv_codes: string[];
  languages: string[];
  minimum_contract_value: string | null;
  maximum_contract_value: string | null;
  company_size: string | null;
};

export type Match = {
  id: string;
  tender_id: string;
  overall_score: number;
  component_scores: Record<string, number>;
  reasons: string[];
  blockers: string[];
  tender: Tender | null;
};

export type SavedTender = { id: string; tender_id: string; notes: string | null; tender: Tender };

export type DocumentSource = {
  id: string;
  source_url: string;
  file_name: string | null;
  media_type: string | null;
  processing_status: string;
  extracted_at: string | null;
  chunk_count: number;
};

export type Analysis = {
  tender_id: string;
  summary: string;
  key_requirements: string[];
  potential_blockers: string[];
  required_documents: string[];
  evaluation_criteria: string[];
  generation_method: string;
};

export type Answer = {
  answer: string;
  status: string;
  citations: Array<{ chunk_id: string; source_url: string; excerpt: string; page_number: number | null }>;
  retrieval_method: string;
};

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api/v1${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(detail?.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const formatMoney = (value: string | null, currency: string | null) => {
  if (!value) return "Not published";
  return new Intl.NumberFormat("en-BE", { style: "currency", currency: currency || "EUR", maximumFractionDigits: 0 }).format(Number(value));
};

export const formatDate = (value: string | null) => value
  ? new Intl.DateTimeFormat("en-BE", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value))
  : "Not published";
