# ADR-001: Evaluation Engine independente da interface web

## Status
Aceito

## Contexto
O Evaluation Engine precisa ser executável via CLI, testes automatizados e
futuramente via API, sem depender de estar rodando dentro de um processo Next.js.

## Decisão
O Evaluation Engine (Python) é uma biblioteca/CLI standalone em `engine/`, sem
nenhuma dependência de `apps/web`. A comunicação com o frontend (Fase V1) acontece
via API (`apps/api`) ou arquivos de resultado persistidos, nunca por import direto.

## Consequências
- Permite rodar avaliações em CI sem subir o frontend.
- Exige um contrato estável entre Engine e API (ver `docs/specs/evaluation-engine/contracts/`).
