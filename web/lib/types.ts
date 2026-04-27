// API types — mirror server/main.py pydantic models

export type RowSource = "vision" | "rule" | "catalog" | "spec_table" | "human";
export type Category = "목대" | "상품";

export interface RuleCitation {
  rule_id: string;
  description: string;
  document: string;
  page: number | null;
  section_code: string | null;
}

export interface CabinetRow {
  index: number;
  category: Category;
  code: string;
  name: string;
  width_mm: number | null;
  depth_mm: number | null;
  height_mm: number | null;
  type_label: string;
  source: RowSource;
  confidence: number;
  rule_citation: RuleCitation | null;
}

export interface Validation {
  rule_id: string;
  description: string;
  passed: boolean;
  detail: string;
}

export interface VariantSummary {
  code: string;
  label: string;
  page_number: number;
  units: number;
  rows_count: number;
  flagged: number;
  is_approved: boolean;
}

export interface VariantDetail {
  code: string;
  label: string;
  page_number: number;
  units: number;
  rows: CabinetRow[];
  validations: Validation[];
  rules_fired: string[];
  is_approved: boolean;
}

export interface ProjectSummary {
  id: string;
  name: string;
  developer: string;
  variants_count: number;
  units_total: number;
  approved_variants: number;
  status: string;
  created_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  variants: VariantSummary[];
  blueprint_pdf_path: string;
}
