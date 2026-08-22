export type RiskLevel = "low" | "medium" | "high" | "critical";
export type ReviewStatus = "pending" | "confirmed" | "dismissed" | "needs_more_data";

export interface SignalContribution {
  key: string;
  label: string;
  value: number;
  weight: number;
  contribution: number;
  explanation: string;
}

export interface TargetEvidence {
  key: string;
  event_count: number;
  account_count: number;
}

export interface GraphEvidence {
  node_count: number;
  edge_count: number;
  density: number;
  strongest_pairs: [string, string, number][];
}

export interface CoordinationAlert {
  alert_id: string;
  created_at: string;
  window_start: string;
  window_end: string;
  risk_score: number;
  risk_level: RiskLevel;
  summary: string;
  account_ids: string[];
  event_ids: string[];
  signals: SignalContribution[];
  targets: TargetEvidence[];
  graph: GraphEvidence;
  status: ReviewStatus;
  synthetic: boolean;
  engine_version: string;
}

export interface ReplayResult {
  scenario: string;
  event_count: number;
  alert_count: number;
  alerts: CoordinationAlert[];
}
