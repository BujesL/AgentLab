const API_BASE_URL = process.env.API_URL ?? "http://localhost:3001";

export interface Experiment {
  id: string;
  agent_version_id: string;
  dataset_id: string;
  model: string;
  status: string;
}

export interface MetricScore {
  metric: string;
  pct: number;
}

export interface ExperimentSummary {
  experiment_id: string;
  total_cases: number;
  passed: number;
  accuracy_pct: number;
  avg_latency_ms: number;
  avg_cost: number;
  metric_scores: MetricScore[];
}

export async function fetchExperiments(): Promise<Experiment[]> {
  const res = await fetch(`${API_BASE_URL}/experiments`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to fetch experiments: ${res.status}`);
  return res.json();
}

export async function fetchExperimentSummary(id: string): Promise<ExperimentSummary> {
  const res = await fetch(`${API_BASE_URL}/experiments/${id}/summary`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to fetch summary for ${id}: ${res.status}`);
  return res.json();
}

export interface QualityGateResult {
  experiment_id: string;
  policy_name: string;
  passed: boolean;
  rule_results: Array<{
    metric: string;
    operator: string;
    expected: number;
    actual: number | null;
    passed: boolean | null;
  }>;
}

export async function fetchQualityGate(id: string): Promise<QualityGateResult> {
  const res = await fetch(`${API_BASE_URL}/experiments/${id}/quality-gate`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to fetch quality gate for ${id}: ${res.status}`);
  return res.json();
}

export interface TraceListItem {
  id: string;
  case_id: string;
  duration_ms: number;
  cost: number | null;
  passed: boolean | null;
}

export async function fetchExperimentTraces(id: string): Promise<TraceListItem[]> {
  const res = await fetch(`${API_BASE_URL}/experiments/${id}/traces`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to fetch traces for experiment ${id}: ${res.status}`);
  return res.json();
}

export interface TraceEvent {
  sequence: number;
  type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}

export interface TraceDetail {
  id: string;
  experiment_id: string | null;
  case_id: string;
  started_at: number;
  duration_ms: number;
  token_usage: number | null;
  cost: number | null;
  events: TraceEvent[];
}

export async function fetchTrace(id: string): Promise<TraceDetail> {
  const res = await fetch(`${API_BASE_URL}/traces/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to fetch trace ${id}: ${res.status}`);
  return res.json();
}
