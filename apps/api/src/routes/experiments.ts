import type { FastifyInstance } from "fastify";
import type { Pool } from "pg";

export async function experimentsRoutes(app: FastifyInstance, opts: { pool: Pool }) {
  const { pool } = opts;

  app.get("/experiments", async () => {
    const result = await pool.query(
      "SELECT id, agent_version_id, dataset_id, model, status FROM experiment ORDER BY id ASC"
    );
    return result.rows;
  });

  app.get<{ Params: { id: string } }>("/experiments/:id/summary", async (request, reply) => {
    const { id } = request.params;

    const countsResult = await pool.query(
      "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE passed) AS passed " +
        "FROM evaluation_result WHERE experiment_id = $1",
      [id]
    );
    const avgResult = await pool.query(
      "SELECT AVG(duration_ms) AS avg_latency_ms, AVG(cost) AS avg_cost " +
        "FROM trace WHERE experiment_id = $1",
      [id]
    );

    const total = Number(countsResult.rows[0].total);
    const passed = Number(countsResult.rows[0].passed);
    const accuracyPct = total > 0 ? (passed / total) * 100 : 0;
    const avgLatencyMs = avgResult.rows[0].avg_latency_ms
      ? Number(avgResult.rows[0].avg_latency_ms)
      : 0;
    const avgCost = avgResult.rows[0].avg_cost ? Number(avgResult.rows[0].avg_cost) : 0;

    return {
      experiment_id: id,
      total_cases: total,
      passed,
      accuracy_pct: accuracyPct,
      avg_latency_ms: avgLatencyMs,
      avg_cost: avgCost,
    };
  });
}
