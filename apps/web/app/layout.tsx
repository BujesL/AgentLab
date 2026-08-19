import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent Evaluation Lab",
  description: "Plataforma de avaliação reproduzível de agentes de IA",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
