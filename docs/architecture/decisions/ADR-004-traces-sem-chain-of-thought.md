# ADR-004: Traces nunca carregam chain-of-thought privado

## Status
Aceito

## Contexto
O documento-base (seção 3, 14, 15) exige que o Trace Viewer não exponha
raciocínio privado do modelo — apenas input, tool calls, resultados, resposta
final e métricas.

## Decisão
`TraceEvent.payload` só pode conter dados observáveis (input do usuário, nome e
argumentos de tool call, resultado de tool, resposta final). `build_trace()`
valida recursivamente que nenhuma chave de payload se chama `reasoning`,
`thought` ou `chain_of_thought` (case-insensitive), levantando erro se
encontrar — mesmo que nenhum provider atual produza esse campo, a validação
existe para que a introdução futura de um provider real (Claude, etc.) não
vaze isso silenciosamente.

## Consequências
- Qualquer `ProviderAdapter` real que exponha campos de raciocínio no seu
  retorno precisa filtrá-los antes de virar `ToolCallRequest`/`FinalAnswer` —
  a validação em `build_trace` funciona como uma rede de segurança, não como
  o único filtro (o adapter também deve ser revisado).
- Testes de `test_traces.py` cobrem isso explicitamente.
