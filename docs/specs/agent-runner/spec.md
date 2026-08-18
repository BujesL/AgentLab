# Spec: Agent Runner + Provider Adapter

Status: **em desenvolvimento (MVP)**

## Problema

Precisamos executar um `EvaluationCase` contra um agente real (ou mockado) de forma
uniforme, independente de qual LLM está por trás (Claude, OpenAI, Gemini —
seção 8/ADR-002), e independente de quais ferramentas existem. O resultado dessa
execução (quais tools foram chamadas, com quais argumentos, e a resposta final)
é o insumo bruto para o Evaluation Engine (métricas) e para o Trace Model
(próxima spec).

## Resultado esperado

1. Uma interface `ProviderAdapter` que abstrai "enviar input + tools disponíveis,
   receber tool calls e/ou resposta final", sem o Agent Runner saber qual provider
   está por trás (ADR-002: comunicação entre camadas via contrato, não import
   direto).
2. Um `ToolRegistry` que define quais ferramentas existem, seus schemas de
   input/output, `risk_level` e `requires_approval` (seção 13 do documento-base).
3. Um `AgentRunner` que recebe um `EvaluationCase` + `ProviderAdapter` +
   `ToolRegistry`, executa, e devolve um `RunResult` bruto (lista de tool calls
   feitas + resposta final) — sem calcular métricas ainda (isso é
   responsabilidade do Evaluation Engine, spec futura).
4. Um `MockProviderAdapter` determinístico para testes, que não faz nenhuma
   chamada de rede — necessário porque ADR-005 (ferramentas reais bloqueadas por
   padrão em avaliações) e porque testes de CI não devem depender de API key/custo
   real.
5. Ferramentas **mockadas por padrão** (`enabled_for_evaluation: true` mas sem
   efeito colateral real) — alinhado à seção 14 (Segurança): "preferir
   mocks/sandboxes nos datasets", "ferramentas reais somente com autorização
   explícita".

## Escopo

### Dentro do escopo (MVP)

- `ProviderAdapter` (ABC) com um único método de execução.
- `ToolSpec` / `ToolRegistry` com schema (seção 13), mas SEM chamada real de tool —
  execução de tool no MVP é sempre mockada (retorna dado stub definido no próprio
  registro do teste).
- `MockProviderAdapter` — permite rodar o pipeline inteiro sem custo/rede.
- `AgentRunner.run()` — orquestra: manda input+tools pro provider, se o provider
  pedir uma tool call, executa a tool (mockada) e devolve resultado ao provider,
  repete até resposta final ou limite de iterações.
- `RunResult`: lista de tool calls (nome, argumentos, resultado) + resposta final.

### Fora do escopo (fases/specs futuras)

- `ClaudeProviderAdapter` real (chamada à API Anthropic) — próxima iteração desta
  mesma spec, após o contrato estar validado com o mock; ou entra junto do CLI
  (etapa 9 do roadmap). Não é bloqueante para o restante do MVP porque as métricas
  podem ser validadas com o mock.
- Execução de ferramentas reais (com efeito colateral) — nunca no MVP (ADR-005).
- Trace Model formal (eventos com timestamp, sequência, payload) — próxima spec;
  aqui produzimos apenas o `RunResult` bruto que o Trace Collector vai consumir.
- Aprovação humana (`requires_approval`) como fluxo interativo — no MVP, um caso
  com `requires_approval: true` é tratado como "não executar automaticamente",
  o runner reporta a necessidade de aprovação e não chama a tool.

## Critérios de aceitação

- [ ] `ProviderAdapter` é uma interface abstrata; qualquer implementação concreta
      (mock ou real) é intercambiável sem mudar o `AgentRunner`.
- [ ] `AgentRunner.run()` com `MockProviderAdapter` executa um caso de
      `expected_tools: []` sem tentar chamar nenhuma ferramenta.
- [ ] `AgentRunner.run()` executa um caso com `expected_tools` não vazio, chama a
      tool mockada, e repassa o resultado da tool de volta ao provider antes da
      resposta final.
- [ ] Um caso com `requires_approval: true` NÃO executa a tool automaticamente —
      o `RunResult` indica `blocked_pending_approval: true`.
- [ ] `ToolRegistry` rejeita registro de tool sem `input_schema`.
- [ ] `RunResult` captura tool calls na ordem em que ocorreram.
