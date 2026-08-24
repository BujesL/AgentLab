import Link from "next/link";
import { fetchExperimentTraces, type TraceListItem } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ExperimentTracesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let traces: TraceListItem[];
  let error: string | null = null;
  try {
    traces = await fetchExperimentTraces(id);
  } catch (e) {
    traces = [];
    error = e instanceof Error ? e.message : "erro desconhecido ao buscar traces";
  }

  return (
    <main className="min-h-screen bg-[#0b0b0d] px-6 py-10 text-white">
      <div className="mx-auto max-w-3xl">
        <Link href="/dashboard" className="text-xs text-white/40 hover:text-white/70">
          ← Experiments
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">Traces</h1>
        <p className="mt-1 text-xs text-white/40">experiment {id}</p>

        {error && (
          <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            Não foi possível buscar traces ({error}).
          </p>
        )}

        <div className="mt-6 divide-y divide-white/10 rounded-lg border border-white/10">
          {traces.length === 0 && !error && (
            <p className="px-4 py-6 text-sm text-white/50">Nenhum trace para este experimento.</p>
          )}
          {traces.map((t) => (
            <Link
              key={t.id}
              href={`/traces/${t.id}`}
              className="flex items-center justify-between px-4 py-3 text-sm hover:bg-white/5"
            >
              <span className="font-mono text-white/80">{t.case_id}</span>
              <span className="flex items-center gap-4 text-white/40">
                <span>{t.duration_ms.toFixed(0)}ms</span>
                <span
                  className={
                    t.passed === null
                      ? "text-white/40"
                      : t.passed
                        ? "text-emerald-400"
                        : "text-red-400"
                  }
                >
                  {t.passed === null ? "?" : t.passed ? "PASS" : "FAIL"}
                </span>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
