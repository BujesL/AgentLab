# Spec: Token, Latency e Cost Tracking

Status: **em desenvolvimento (MVP)**

## Problema

O `Trace` (spec anterior) já tem `duration_ms` (latência) preenchido, mas
`token_usage` e `cost` ficam sempre `None` — não há como comparar custo/consumo
entre modelos (seção 17, "Comparação de modelos") sem isso.

## Resultado esperado

1. `ProviderAdapter` pode reportar uso de tokens (`prompt_tokens`,
   `completion_tokens`) a cada passo (`ProviderStep`).
2. `AgentRunner` agrega o uso de tokens de todos os passos de uma execução em
   `RunResult.token_usage`.
3. Uma tabela de preço por modelo (`engine/cost.py`) calcula custo estimado a
   partir do uso agregado.
4. `build_trace()` popula `Trace.token_usage` (total de tokens) e `Trace.cost`
   quando há uso reportado.

## Decisão importante: preços são placeholder, não tarifário oficial

A tabela de preços (`PRICING` em `engine/cost.py`) usa valores de exemplo para
viabilizar o cálculo e os testes — **não são os preços reais e atuais da API
Anthropic/OpenAI**. Antes de usar este cálculo para decisões reais de custo em
produção, a tabela precisa ser atualizada com os valores oficiais vigentes do
provedor (isso é responsabilidade de quem operar o sistema, documentado aqui
para não ser confundido com dado real).

## Escopo

### Dentro do escopo (MVP)

- `TokenUsage` (prompt_tokens, completion_tokens, total_tokens calculado).
- `ProviderStep` (ToolCallRequest/FinalAnswer) ganham campo opcional `usage`.
- Agregação no `AgentRunner` (soma de todos os passos da execução).
- `estimate_cost(usage, model) -> float` com tabela de preços placeholder e
  fallback para modelo desconhecido (preço "mock" = 0).
- `Trace.token_usage`/`Trace.cost` populados quando há uso reportado; `None`
  quando não há (ex. um `MockProviderAdapter` de teste que não reporta usage).

### Fora do escopo (fases futuras)

- Preços reais/atualizados automaticamente via API do provedor — não faz
  parte do MVP; requer manutenção manual da tabela ou integração futura.
- Cost tracking por experimento agregado (soma de N execuções) — depende do
  Experiment Manager (fase posterior).

## Critérios de aceitação

- [ ] Uma execução onde nenhum passo reporta `usage` produz
      `RunResult.token_usage is None` e, consequentemente,
      `Trace.token_usage is None` e `Trace.cost is None`.
- [ ] Uma execução com múltiplos passos reportando `usage` agrega
      `prompt_tokens`/`completion_tokens` corretamente (soma).
- [ ] `estimate_cost` retorna 0.0 para o modelo `"mock"` mesmo com tokens > 0.
- [ ] `estimate_cost` retorna um valor > 0 para um modelo com preço > 0 na
      tabela e uso de tokens > 0.
- [ ] `estimate_cost` não lança erro para um nome de modelo desconhecido —
      cai no fallback `"mock"` (preço 0), fail-safe em vez de fail-loud aqui
      porque um modelo desconhecido não deve travar a avaliação inteira, só
      não reportar custo confiável.
- [ ] `build_trace` propaga `token_usage`/`cost` corretamente para o `Trace`.
