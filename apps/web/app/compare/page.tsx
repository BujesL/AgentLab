import { fetchExperimentSummary, fetchExperiments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ a?: string; b?: string }>;
}) {
  const { a, b } = await searchParams;
  const experiments = await fetchExperiments().catch(() => []);

  const summaryA = a ? await fetchExperimentSummary(a).catch(() => null) : null;
  const summaryB = b ? await fetchExperimentSummary(b).catch(() => null) : null;

  // Union of every metric key reported by either side — new evaluator metrics
  // (groundedness, answer_accuracy_llm_judge, ...) show up automatically, no
  // hardcoded list to keep in sync.
  const metricNames = Array.from(
    new Set([
      ...(summaryA?.metric_scores.map((m) => m.metric) ?? []),
      ...(summaryB?.metric_scores.map((m) => m.metric) ?? []),
    ])
  ).sort();

  return (
    <main className="min-h-screen bg-[#0b0b0d] px-6 py-10 text-white">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Comparar experimentos</h1>
        <p className="mt-2 text-sm text-white/50">
          Passe dois ids de experimento na URL: <code>?a=ID1&b=ID2</code>
        </p>

        <div className="mt-6 flex flex-wrap gap-2 text-xs text-white/40">
          {experiments.map((exp) => (
            <span key={exp.id} className="rounded border border-white/10 px-2 py-1">
              {exp.id.slice(0, 8)}… ({exp.dataset_id}/{exp.model})
            </span>
          ))}
        </div>

        <table className="mt-8 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-white/50">
              <th className="py-2">Métrica</th>
              <th className="py-2">{a ? a.slice(0, 8) + "…" : "A"}</th>
              <th className="py-2">{b ? b.slice(0, 8) + "…" : "B"}</th>
            </tr>
          </thead>
          <tbody>
            <Row label="Total cases" a={summaryA?.total_cases} b={summaryB?.total_cases} />
            <Row label="Passed" a={summaryA?.passed} b={summaryB?.passed} />
            <Row
              label="Accuracy"
              a={summaryA ? `${summaryA.accuracy_pct.toFixed(1)}%` : undefined}
              b={summaryB ? `${summaryB.accuracy_pct.toFixed(1)}%` : undefined}
            />
            <Row
              label="Avg Latency"
              a={summaryA ? `${summaryA.avg_latency_ms.toFixed(2)}ms` : undefined}
              b={summaryB ? `${summaryB.avg_latency_ms.toFixed(2)}ms` : undefined}
            />
            <Row
              label="Avg Cost"
              a={summaryA ? `$${summaryA.avg_cost.toFixed(4)}` : undefined}
              b={summaryB ? `$${summaryB.avg_cost.toFixed(4)}` : undefined}
            />
            {metricNames.map((metric) => {
              const scoreA = summaryA?.metric_scores.find((m) => m.metric === metric)?.pct;
              const scoreB = summaryB?.metric_scores.find((m) => m.metric === metric)?.pct;
              return (
                <Row
                  key={metric}
                  label={metric}
                  a={scoreA !== undefined ? `${scoreA.toFixed(1)}%` : undefined}
                  b={scoreB !== undefined ? `${scoreB.toFixed(1)}%` : undefined}
                />
              );
            })}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function Row({
  label,
  a,
  b,
}: {
  label: string;
  a: string | number | undefined;
  b: string | number | undefined;
}) {
  return (
    <tr className="border-b border-white/5">
      <td className="py-2 text-white/70">{label}</td>
      <td className="py-2">{a ?? "—"}</td>
      <td className="py-2">{b ?? "—"}</td>
    </tr>
  );
}
