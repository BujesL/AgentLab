import type { FastifyInstance } from "fastify";
import type { Pool } from "pg";

export async function tracesRoutes(app: FastifyInstance, opts: { pool: Pool }) {
  const { pool } = opts;

  app.get<{ Params: { id: string } }>("/traces/:id", async (request, reply) => {
    const { id } = request.params;

    const traceResult = await pool.query(
      "SELECT id, experiment_id, case_id, started_at, duration_ms, token_usage, cost " +
        "FROM trace WHERE id = $1",
      [id]
    );

    if (traceResult.rowCount === 0) {
      reply.code(404);
      return { error: "trace not found" };
    }

    const eventsResult = await pool.query(
      "SELECT sequence, type, payload, timestamp FROM trace_event " +
        "WHERE trace_id = $1 ORDER BY sequence ASC",
      [id]
    );

    const row = traceResult.rows[0];
    return {
      id: row.id,
      experiment_id: row.experiment_id,
      case_id: row.case_id,
      started_at: Number(row.started_at),
      duration_ms: Number(row.duration_ms),
      token_usage: row.token_usage,
      cost: row.cost !== null ? Number(row.cost) : null,
      events: eventsResult.rows.map((e) => ({
        sequence: e.sequence,
        type: e.type,
        payload: e.payload,
        timestamp: Number(e.timestamp),
      })),
    };
  });
}
