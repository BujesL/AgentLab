# Spec: Trace Model

Status: **em desenvolvimento (MVP)**

## Problema

O `RunResult` da spec anterior (Agent Runner) carrega um `raw_events` genérico —
suficiente para o Evaluation Engine calcular métricas, mas insuficiente para o
Trace Viewer (seção 15 do documento-base), que precisa de sequência numerada,
timestamps e duração por evento, prontos para exibição/auditoria.

## Resultado esperado

1. Um modelo `Trace` + `TraceEvent` formal (Pydantic), alinhado ao modelo
   conceitual de dados (seção 9): `trace(id, experiment_id, case_id, started_at,
   duration, token_usage, cost)` e `trace_event(id, trace_id, type, sequence,
   payload, duration)`.
2. Uma função `build_trace(run_result, case) -> Trace` que converte o
   `RunResult` bruto em um `Trace` com eventos sequenciados e timestamped.
3. Garantia estrutural de que nenhum evento carrega raciocínio privado do
   modelo (chain-of-thought) — só tipo, payload observável (input, tool
   call, tool result, resposta final) e timing.

## Escopo

### Dentro do escopo (MVP)

- `TraceEvent`: sequence, type (`input | tool_call_request | tool_result |
  final_answer | blocked_pending_approval`), payload, timestamp.
- `Trace`: id, case_id, started_at, duration_ms, events. `experiment_id`,
  `token_usage`, `cost` existem no schema mas ficam `None`/vazios no MVP —
  populados nas etapas seguintes (Experiment Manager e Token/Cost tracking,
  itens 27/29 do roadmap).
- `AgentRunner` passa a registrar timestamp em cada evento de `raw_events`
  (mudança mínima retroativa na spec anterior, documentada aqui).
- Validação estrutural: nenhuma chave dos payloads deve se chamar `reasoning`,
  `thought`, `chain_of_thought` ou similar (checagem defensiva, mesmo que o
  `MockProviderAdapter`/futuros adapters não produzam isso hoje).

### Fora do escopo (fases futuras)

- Persistência em PostgreSQL do trace — spec futura (item 30 do roadmap:
  "Persistir resultados em PostgreSQL").
- Trace Viewer (UI) — Fase V1 (Frontend Engineer, seção 5).
- Redação/mascaramento de dados sensíveis nos payloads — Fase de segurança
  avançada (seção 14, item mencionado mas não crítico enquanto os dados são
  mockados/sintéticos no MVP).

## Critérios de aceitação

- [ ] `build_trace()` produz eventos com `sequence` estritamente crescente
      começando em 0.
- [ ] O primeiro evento é sempre `type == "input"`.
- [ ] O último evento reflete o desfecho real do `RunResult`
      (`final_answer` ou `blocked_pending_approval`).
- [ ] `duration_ms` é sempre >= 0 e igual à diferença entre o timestamp do
      último e do primeiro evento.
- [ ] Nenhum payload de nenhum evento contém as chaves proibidas
      (`reasoning`, `thought`, `chain_of_thought`) — testado explicitamente.
- [ ] Um `RunResult` com múltiplas tool calls produz eventos
      `tool_call_request`/`tool_result` intercalados na ordem correta.
