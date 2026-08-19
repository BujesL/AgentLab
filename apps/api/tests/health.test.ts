import { describe, expect, it } from "vitest";
import { buildServer } from "../src/server.js";

describe("GET /health", () => {
  it("returns 200 with status ok, without touching the database", async () => {
    const fakePool = {} as never; // health route never queries the pool
    const app = await buildServer({ pool: fakePool, repoRoot: process.cwd() });

    const response = await app.inject({ method: "GET", url: "/health" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ status: "ok" });

    await app.close();
  });
});
