# Spec: Persistência PostgreSQL (Trace + Evaluation Result)

Status: **em desenvolvimento (MVP)**

## Problema

Até aqui `Trace` e `EvaluationResult` só existem em memória, dentro de um
processo Python. Para comparar execuções (seção 16/17/19 do documento-base) e
para o item 30 do roadmap ("Persistir resultados em PostgreSQL"), eles precisam
sobreviver ao fim do processo.

## Escopo reduzido em relação ao modelo conceitual completo (seção 9)

O modelo de dados completo do documento-base inclui `agent`, `agent_version`,
`experiment`, `prompt_version` — todas dependem do **Experiment Manager**, que
ainda não existe (é uma spec futura, pós-CLI). Persistir essas tabelas agora
seria construir sobre um conceito que ainda não foi desenhado.

Este MVP persiste apenas o que já existe como conceito maduro:
- `dataset` (metadados do dataset usado — id/name/version, não os casos em si,
  que continuam vivendo em `datasets/*.json` como fonte de verdade)
- `trace` + `trace_event`
- `evaluation_result`

Quando o Experiment Manager for especificado (próxima fase), essas tabelas
ganham uma FK `experiment_id` (já existe como coluna opcional nullable em
`Trace`, seção 9). Isso evita retrabalho de migração mais tarde.

## Resultado esperado

1. `docker-compose.yml` com um serviço PostgreSQL local para desenvolvimento.
2. Schema SQL (`engine/persistence/schema.sql`) criando as tabelas
   `dataset`, `trace`, `trace_event`, `evaluation_result`.
3. Uma camada de acesso (`engine/persistence/repository.py`) com funções
   `save_trace`, `save_evaluation_result`, `get_trace`, `list_evaluation_results`
   — sem ORM pesado (psycopg puro), para manter o Evaluation Engine leve
   (ADR-001: independente de frameworks web).
4. Configuração via variável de ambiente `DATABASE_URL` (nunca hardcoded —
   seção 14, "nunca salvar API keys/segredos no repositório", princípio que
   estendemos a credenciais de banco).
5. Testes de integração que rodam contra um Postgres real (via
   `docker-compose`), não mockado — porque o objetivo aqui é validar SQL e
   schema reais, não a lógica de negócio (essa já está testada nas specs
   anteriores com testes unitários puros).

## Critérios de aceitação

- [ ] `docker-compose up -d` sobe um Postgres acessível localmente.
- [ ] O schema é aplicável via script idempotente (`CREATE TABLE IF NOT EXISTS`).
- [ ] `save_trace(trace)` persiste um `Trace` e todos os seus `TraceEvent`
      associados (FK `trace_id`).
- [ ] `get_trace(trace_id)` reconstrói um `Trace` idêntico ao persistido
      (round-trip), incluindo a ordem dos eventos por `sequence`.
- [ ] `save_evaluation_result(result)` persiste um `EvaluationResult`,
      incluindo o dict `scores` (serializado como JSONB).
- [ ] `list_evaluation_results(case_id=None)` retorna resultados filtráveis
      por caso.
- [ ] Rodar o schema duas vezes seguidas não falha (idempotência).
