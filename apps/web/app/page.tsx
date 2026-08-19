import Link from "next/link";
import KineticGrid from "@/components/ui/kinetic-grid";

export default function HomePage() {
  return (
    <KineticGrid>
      <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
        <span className="mb-5 rounded-full border border-white/15 px-3 py-1 text-xs font-medium tracking-wide text-white/70">
          AI Engineering · Agent Evaluation
        </span>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-6xl">
          Agent Evaluation Lab
        </h1>
        <p className="mt-4 max-w-md text-base text-white/50">
          Uma plataforma de engenharia para avaliação sistemática, reprodutível
          e rastreável de agentes de IA.
        </p>
        <Link
          href="/dashboard"
          className="mt-8 rounded-full bg-white px-6 py-2 text-sm font-medium text-black transition hover:bg-white/90"
        >
          Ver experimentos
        </Link>
      </div>
    </KineticGrid>
  );
}
