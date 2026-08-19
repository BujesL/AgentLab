import { fetchExperiments, fetchExperimentSummary, type Experiment } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let experiments: Experiment[];
  let error: string | null = null;

  try {
    experiments = await fetchExperiments();
  } catch (e) {
    experiments = [];
    error = e instanceof Error ? e.message : "erro desconhecido ao buscar experimentos";
  }

  const summaries = error
    ? []
    : await Promise.all(
        experiments.map(async (exp) => {
          try {
            return await fetchExperimentSummary(exp.id);
          } catch {
            return null;
          }
        })
      );

  const validSummaries = summaries.filter((s): s is NonNullable<typeof s> => s !== null);
  const totalEvaluations = validSummaries.reduce((sum, s) => sum + s.total_cases, 0);
  const overallAccuracy =
    validSummaries.length > 0
      ? validSummaries.reduce((sum, s) => sum + s.accuracy_pct, 0) / validSummaries.length
      : 0;
  const avgCost =
    validSummaries.length > 0
      ? validSummaries.reduce((sum, s) => sum + s.avg_cost, 0) / validSummaries.length
      : 0;
  const avgLatency =
    validSummaries.length > 0
      ? validSummaries.reduce((sum, s) => sum + s.avg_latency_ms, 0) / validSummaries.length
      : 0;

  return (
    <main className="min-h-screen bg-[#0b0b0d] px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-2xl font-semibold">AGENT EVALUATION</h1>

        {error && (
          <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            Não foi possível conectar à API ({error}). Verifique se ela está
            rodando em {process.env.API_URL ?? "http://localhost:3001"}.
          </p>
        )}

        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <Stat label="Experiments" value={experiments.length.toString()} />
          <Stat label="Evaluations" value={totalEvaluations.toString()} />
          <Stat label="Accuracy" value={`${overallAccuracy.toFixed(1)}%`} />
          <Stat label="Avg Cost" value={`$${avgCost.toFixed(4)}`} />
          <Stat label="Avg Latency" value={`${avgLatency.toFixed(2)}ms`} />
        </div>

        <h2 className="mt-10 text-lg font-medium">Recent Experiments</h2>
        <div className="mt-4 divide-y divide-white/10 rounded-lg border border-white/10">
          {experiments.length === 0 && !error && (
            <p className="px-4 py-6 text-sm text-white/50">
              Nenhum experimento ainda. Rode <code>agentlab evaluate --agent ...</code>{" "}
              para criar um.
            </p>
          )}
          {experiments.map((exp, i) => {
            const summary = summaries[i];
            const passed = summary ? summary.accuracy_pct === 100 : null;
            return (
              <div
                key={exp.id}
                className="flex items-center justify-between px-4 py-3 text-sm"
              >
                <div>
                  <p className="font-medium">{exp.dataset_id}</p>
                  <p className="text-white/40">{exp.model}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-white/70">
                    {summary ? `${summary.accuracy_pct.toFixed(1)}%` : "—"}
                  </span>
                  <span
                    className={
                      passed === null
                        ? "text-white/40"
                        : passed
                          ? "text-emerald-400"
                          : "text-red-400"
                    }
                  >
                    {passed === null ? "?" : passed ? "PASS" : "FAIL"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 px-4 py-3">
      <p className="text-xs text-white/40">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
