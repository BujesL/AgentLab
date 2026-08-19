const API_BASE_URL = process.env.API_URL ?? "http://localhost:3001";

export interface Experiment {
  id: string;
  agent_version_id: string;
  dataset_id: string;
  model: string;
  status: string;
}

export interface ExperimentSummary {
  experiment_id: string;
  total_cases: number;
  passed: number;
  accuracy_pct: number;
  avg_latency_ms: number;
  avg_cost: number;
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
