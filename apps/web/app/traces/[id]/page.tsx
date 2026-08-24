import Link from "next/link";
import { fetchTrace, type TraceEvent } from "@/lib/api";

export const dynamic = "force-dynamic";

const EVENT_LABELS: Record<string, string> = {
  input: "INPUT",
  retrieval: "RETRIEVAL",
  handoff: "HANDOFF",
  tool_call_request: "TOOL CALL",
  tool_result: "TOOL RESULT",
  blocked_pending_approval: "BLOCKED (approval)",
  final_answer: "FINAL ANSWER",
};

export default async function TracePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let trace;
  let error: string | null = null;
  try {
    trace = await fetchTrace(id);
  } catch (e) {
    trace = null;
    error = e instanceof Error ? e.message : "erro desconhecido ao buscar trace";
  }

  return (
    <main className="min-h-screen bg-[#0b0b0d] px-6 py-10 text-white">
      <div className="mx-auto max-w-3xl">
        {trace?.experiment_id && (
          <Link
            href={`/experiments/${trace.experiment_id}/traces`}
            className="text-xs text-white/40 hover:text-white/70"
          >
            ← Traces
          </Link>
        )}
        <h1 className="mt-2 text-2xl font-semibold">Trace</h1>
        <p className="mt-1 font-mono text-xs text-white/40">{id}</p>

        {error && (
          <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            Não foi possível buscar o trace ({error}).
          </p>
        )}

        {trace && (
          <>
            <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
              <Stat label="Case" value={trace.case_id} />
              <Stat label="Duration" value={`${trace.duration_ms.toFixed(0)}ms`} />
              <Stat
                label="Cost"
                value={trace.cost !== null ? `$${trace.cost.toFixed(4)}` : "—"}
              />
            </div>

            <ol className="mt-8 space-y-2">
              {trace.events.map((event) => (
                <EventRow key={event.sequence} event={event} />
              ))}
            </ol>
          </>
        )}
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 px-4 py-3">
      <p className="text-xs text-white/40">{label}</p>
      <p className="mt-1 font-mono text-sm">{value}</p>
    </div>
  );
}

function EventRow({ event }: { event: TraceEvent }) {
  const label = EVENT_LABELS[event.type] ?? event.type.toUpperCase();

  // Handoff gets a dedicated layout (from -> to pill) instead of raw JSON — it's the
  // one event type that's specifically about routing between agents, not tool I/O.
  if (event.type === "handoff") {
    const from = String(event.payload.from ?? "?");
    const to = event.payload.to ? String(event.payload.to) : null;
    return (
      <li className="rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-3 text-sm">
        <span className="font-mono text-xs uppercase tracking-wide text-sky-400">{label}</span>
        <div className="mt-1 flex items-center gap-2 font-mono text-white/80">
          <span className="rounded bg-white/10 px-2 py-0.5">{from}</span>
          <span className="text-white/30">→</span>
          {to ? (
            <span className="rounded bg-sky-500/20 px-2 py-0.5">{to}</span>
          ) : (
            <span className="rounded bg-red-500/20 px-2 py-0.5 text-red-300">
              sem especialista ({String(event.payload.error ?? "erro de roteamento")})
            </span>
          )}
        </div>
      </li>
    );
  }

  return (
    <li className="rounded-lg border border-white/10 px-4 py-3 text-sm">
      <span className="font-mono text-xs uppercase tracking-wide text-white/40">{label}</span>
      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-words font-mono text-xs text-white/70">
        {JSON.stringify(event.payload, null, 2)}
      </pre>
    </li>
  );
}
