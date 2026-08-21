import { randomUUID } from "node:crypto";
import type { Pool } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createPool } from "../src/db.js";
import { buildServer } from "../src/server.js";

const hasDb = Boolean(process.env.DATABASE_URL);
const describeIfDb = hasDb ? describe : describe.skip;

describeIfDb("GET /experiments and /experiments/:id/summary", () => {
  let pool: Pool;
  let app: Awaited<ReturnType<typeof buildServer>>;
  let agentId: string;
  let versionId: string;

  beforeAll(async () => {
    pool = createPool();
    app = await buildServer({ pool, repoRoot: process.cwd() });

    agentId = randomUUID();
    versionId = randomUUID();
    await pool.query("INSERT INTO agent (id, name) VALUES ($1, $2)", [
      agentId,
      `test-agent-${agentId}`,
    ]);
    await pool.query(
      "INSERT INTO agent_version (id, agent_id, version) VALUES ($1, $2, $3)",
      [versionId, agentId, "1.0.0"]
    );
  });

  afterAll(async () => {
    await pool.query("DELETE FROM agent WHERE id = $1", [agentId]);
    await app.close();
    await pool.end();
  });

  it("lists experiments as an array", async () => {
    const response = await app.inject({ method: "GET", url: "/experiments" });

    expect(response.statusCode).toBe(200);
    expect(Array.isArray(response.json())).toBe(true);
  });

  it("summarizes an experiment with no data as zeros, not an error", async () => {
    const experimentId = randomUUID();
    await pool.query(
      "INSERT INTO experiment (id, agent_version_id, dataset_id, model) VALUES ($1, $2, $3, $4)",
      [experimentId, versionId, "service-desk-mvp", "mock"]
    );

    const response = await app.inject({
      method: "GET",
      url: `/experiments/${experimentId}/summary`,
    });

    expect(response.statusCode).toBe(200);
    const body = response.json();
    expect(body.total_cases).toBe(0);
    expect(body.accuracy_pct).toBe(0);
    expect(body.metric_scores).toEqual([]);

    await pool.query("DELETE FROM experiment WHERE id = $1", [experimentId]);
  });

  it("summarizes an experiment with real data matching manual computation", async () => {
    const experimentId = randomUUID();
    await pool.query(
      "INSERT INTO experiment (id, agent_version_id, dataset_id, model) VALUES ($1, $2, $3, $4)",
      [experimentId, versionId, "service-desk-mvp", "mock"]
    );
    await pool.query(
      "INSERT INTO evaluation_result (case_id, experiment_id, scores, passed) VALUES ($1, $2, $3, $4)",
      ["SD-001", experimentId, JSON.stringify({}), true]
    );
    await pool.query(
      "INSERT INTO evaluation_result (case_id, experiment_id, scores, passed) VALUES ($1, $2, $3, $4)",
      ["SD-002", experimentId, JSON.stringify({}), false]
    );

    const response = await app.inject({
      method: "GET",
      url: `/experiments/${experimentId}/summary`,
    });

    const body = response.json();
    expect(body.total_cases).toBe(2);
    expect(body.passed).toBe(1);
    expect(body.accuracy_pct).toBe(50);

    await pool.query("DELETE FROM evaluation_result WHERE experiment_id = $1", [experimentId]);
    await pool.query("DELETE FROM experiment WHERE id = $1", [experimentId]);
  });

  it("breaks accuracy down per metric key found in scores, including V2 metrics", async () => {
    const experimentId = randomUUID();
    await pool.query(
      "INSERT INTO experiment (id, agent_version_id, dataset_id, model) VALUES ($1, $2, $3, $4)",
      [experimentId, versionId, "rag-groundedness-mvp", "mock"]
    );
    await pool.query(
      "INSERT INTO evaluation_result (case_id, experiment_id, scores, passed) VALUES ($1, $2, $3, $4)",
      [
        "RAG-001",
        experimentId,
        JSON.stringify({ tool_selection: 1.0, groundedness: 1.0 }),
        true,
      ]
    );
    await pool.query(
      "INSERT INTO evaluation_result (case_id, experiment_id, scores, passed) VALUES ($1, $2, $3, $4)",
      [
        "RAG-002",
        experimentId,
        JSON.stringify({ tool_selection: 1.0, groundedness: 0.0 }),
        false,
      ]
    );

    const response = await app.inject({
      method: "GET",
      url: `/experiments/${experimentId}/summary`,
    });

    const body = response.json();
    const byMetric = Object.fromEntries(
      body.metric_scores.map((m: { metric: string; pct: number }) => [m.metric, m.pct])
    );
    expect(byMetric.tool_selection).toBe(100);
    expect(byMetric.groundedness).toBe(50);

    await pool.query("DELETE FROM evaluation_result WHERE experiment_id = $1", [experimentId]);
    await pool.query("DELETE FROM experiment WHERE id = $1", [experimentId]);
  });
});
