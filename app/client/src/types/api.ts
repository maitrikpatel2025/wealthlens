// These must match the Pydantic models in data_models.py

// ---------------------------------------------------------------------------
// Portfolio data shapes
// ---------------------------------------------------------------------------

export interface HoldingData {
  symbol: string;
  name: string;
  quantity: number;
  market_value: number;
  current_price: number;
  mer: number;
  asset_class: string;
  sector: string;
  country: string;
  geographic_exposure: string;
  market_cap_class: string;
  beta?: number | null;
  dividend_yield?: number | null;
  pe_ratio?: number | null;
}

export interface AccountData {
  name: string;
  type: string;
  total_value: number;
  holdings: HoldingData[];
}

export interface HouseholdData {
  institution: string;
  accounts: AccountData[];
  confidence: number;
}

// ---------------------------------------------------------------------------
// API response types
// ---------------------------------------------------------------------------

export interface UploadStatementResponse {
  institution: string;
  accounts: AccountData[];
  confidence: number;
  widgets: Record<string, unknown>[];
  error?: string;
}

// ---------------------------------------------------------------------------
// UI component shared types (moved from individual components)
// ---------------------------------------------------------------------------

export interface ToolLog {
  id: string | number;
  message: string;
  status: "processing" | "completed";
}

export interface Conversation {
  id: string;
  title: string;
  timestamp: string;
  isActive?: boolean;
}

export interface UsageMeter {
  used: number;
  limit: number;
  label?: string;
}
