import Fastify, { type FastifyInstance } from "fastify";
import type { Pool } from "pg";
import { evaluateRoutes } from "./routes/evaluate.js";
import { experimentsRoutes } from "./routes/experiments.js";
import { healthRoutes } from "./routes/health.js";
import { qualityGateRoutes } from "./routes/quality-gate.js";
import { tracesRoutes } from "./routes/traces.js";

export interface BuildServerOptions {
  pool: Pool;
  repoRoot: string;
}

export async function buildServer(opts: BuildServerOptions): Promise<FastifyInstance> {
  const app = Fastify();

  await app.register(healthRoutes);
  await app.register(experimentsRoutes, { pool: opts.pool });
  await app.register(tracesRoutes, { pool: opts.pool });
  await app.register(evaluateRoutes, { repoRoot: opts.repoRoot });
  await app.register(qualityGateRoutes, { pool: opts.pool, repoRoot: opts.repoRoot });

  return app;
}
