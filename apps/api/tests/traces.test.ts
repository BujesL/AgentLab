import { randomUUID } from "node:crypto";
import type { Pool } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createPool } from "../src/db.js";
import { buildServer } from "../src/server.js";

const hasDb = Boolean(process.env.DATABASE_URL);
const describeIfDb = hasDb ? describe : describe.skip;

describeIfDb("GET /traces/:id", () => {
  let pool: Pool;
  let app: Awaited<ReturnType<typeof buildServer>>;

  beforeAll(async () => {
    pool = createPool();
    app = await buildServer({ pool, repoRoot: process.cwd() });
  });

  afterAll(async () => {
    await app.close();
    await pool.end();
  });

  it("returns 404 for an unknown trace id", async () => {
    const response = await app.inject({
      method: "GET",
      url: `/traces/${randomUUID()}`,
    });

    expect(response.statusCode).toBe(404);
    expect(response.json()).toEqual({ error: "trace not found" });
  });

  it("returns events in sequence order", async () => {
    const traceId = randomUUID();
    await pool.query(
      "INSERT INTO trace (id, case_id, started_at, duration_ms) VALUES ($1, $2, $3, $4)",
      [traceId, "SD-001", 1000.0, 42.0]
    );
    await pool.query(
      "INSERT INTO trace_event (trace_id, sequence, type, payload, timestamp) VALUES ($1, $2, $3, $4, $5)",
      [traceId, 1, "final_answer", JSON.stringify({ answer: { ok: true } }), 1000.04]
    );
    await pool.query(
      "INSERT INTO trace_event (trace_id, sequence, type, payload, timestamp) VALUES ($1, $2, $3, $4, $5)",
      [traceId, 0, "input", JSON.stringify({ input: "oi" }), 1000.0]
    );

    const response = await app.inject({ method: "GET", url: `/traces/${traceId}` });

    expect(response.statusCode).toBe(200);
    const body = response.json();
    expect(body.events.map((e: { type: string }) => e.type)).toEqual([
      "input",
      "final_answer",
    ]);

    await pool.query("DELETE FROM trace WHERE id = $1", [traceId]);
  });
});
