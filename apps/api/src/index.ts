import path from "node:path";
import { fileURLToPath } from "node:url";
import { createPool } from "./db.js";
import { buildServer } from "./server.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../../../");

const pool = createPool();
const app = await buildServer({ pool, repoRoot });

const port = Number(process.env.PORT ?? 3001);
await app.listen({ port, host: "0.0.0.0" });
console.log(`agent-evaluation-lab API listening on :${port}`);
