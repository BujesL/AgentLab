import { spawn } from "node:child_process";
import type { FastifyInstance } from "fastify";

interface EvaluateBody {
  datasetPath: string;
  scriptsPath: string;
  agent?: string;
  agentVersion?: string;
  model?: string;
}

export async function evaluateRoutes(app: FastifyInstance, opts: { repoRoot: string }) {
  const { repoRoot } = opts;

  app.post<{ Body: EvaluateBody }>("/evaluate", async (request, reply) => {
    const { datasetPath, scriptsPath, agent, agentVersion, model } = request.body;

    const args = ["-m", "engine.cli", "evaluate", datasetPath, "--scripts", scriptsPath];
    if (model) args.push("--model", model);
    if (agent) args.push("--agent", agent);
    if (agentVersion) args.push("--agent-version", agentVersion);

    const { exitCode, output } = await runPython(args, repoRoot);

    reply.code(exitCode === 0 ? 200 : 422);
    return { exitCode, output };
  });
}

function runPython(
  args: string[],
  cwd: string,
  timeoutMs = 60_000
): Promise<{ exitCode: number; output: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn("python", args, { cwd });
    let output = "";

    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("evaluate subprocess timed out"));
    }, timeoutMs);

    child.stdout.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      output += chunk.toString();
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ exitCode: code ?? 1, output });
    });
  });
}
