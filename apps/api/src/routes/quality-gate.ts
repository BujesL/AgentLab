import { readFileSync } from "node:fs";
import path from "node:path";
import type { FastifyInstance } from "fastify";
import type { Pool } from "pg";

interface QualityGateRule {
  metric: string;
  operator: ">=" | "<=" | "==";
  value: number;
}

interface QualityGatePolicy {
  name: string;
  rules: QualityGateRule[];
}

const OPERATORS: Record<QualityGateRule["operator"], (a: number, b: number) => boolean> = {
  ">=": (a, b) => a >= b,
  "<=": (a, b) => a <= b,
  "==": (a, b) => a === b,
};

async function getAccuracyPct(pool: Pool, experimentId: string): Promise<number> {
  const result = await pool.query(
    "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE passed) AS passed " +
      "FROM evaluation_result WHERE experiment_id = $1",
    [experimentId]
  );
  const total = Number(result.rows[0].total);
  const passed = Number(result.rows[0].passed);
  return total > 0 ? (passed / total) * 100 : 0;
}

async function getToolSelectionPct(pool: Pool, experimentId: string): Promise<number | null> {
  const result = await pool.query(
    "SELECT AVG((scores->>'tool_selection')::float) * 100 AS pct " +
      "FROM evaluation_result WHERE experiment_id = $1 AND scores ? 'tool_selection'",
    [experimentId]
  );
  const pct = result.rows[0]?.pct;
  return pct !== null && pct !== undefined ? Number(pct) : null;
}

export async function qualityGateRoutes(
  app: FastifyInstance,
  opts: { pool: Pool; repoRoot: string }
) {
  const { pool, repoRoot } = opts;

  app.get<{ Params: { id: string }; Querystring: { baseline?: string; policy?: string } }>(
    "/experiments/:id/quality-gate",
    async (request) => {
      const { id } = request.params;
      const { baseline, policy: policyPath } = request.query;

      const policyFile = policyPath ?? "quality-gates/default.json";
      const policy: QualityGatePolicy = JSON.parse(
        readFileSync(path.join(repoRoot, policyFile), "utf-8")
      );

      const accuracyPct = await getAccuracyPct(pool, id);
      const toolSelectionPct = await getToolSelectionPct(pool, id);

      let regressionDelta: number | null = null;
      if (baseline) {
        const baselineAccuracy = await getAccuracyPct(pool, baseline);
        regressionDelta = accuracyPct - baselineAccuracy;
      }

      const metrics: Record<string, number | null> = {
        accuracy_pct: accuracyPct,
        tool_selection_pct: toolSelectionPct,
        regression_delta: regressionDelta,
      };

      const ruleResults = policy.rules.map((rule) => {
        const actual = metrics[rule.metric];
        if (actual === null || actual === undefined) {
          return { metric: rule.metric, operator: rule.operator, expected: rule.value, actual: null, passed: null };
        }
        const passed = OPERATORS[rule.operator](actual, rule.value);
        return { metric: rule.metric, operator: rule.operator, expected: rule.value, actual, passed };
      });

      const evaluated = ruleResults.filter((r) => r.passed !== null);
      const passed = evaluated.length > 0 && evaluated.every((r) => r.passed);

      return {
        experiment_id: id,
        policy_name: policy.name,
        passed,
        rule_results: ruleResults,
      };
    }
  );
}
