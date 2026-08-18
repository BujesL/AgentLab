# ADR-003: Ferramentas sempre mockadas no MVP; execução real nunca acontece durante avaliação

## Status
Aceito

## Contexto
O documento-base (seção 14, "Segurança") exige que ferramentas reais só rodem com
autorização explícita, e que mocks/sandboxes sejam preferidos nos datasets
(ADR-005 do documento-base original). O `AgentRunner` precisa de uma forma de
"executar" uma tool call sem produzir efeito colateral real, mesmo quando o
provider (LLM) decide chamar uma ferramenta.

## Decisão
No MVP, o `ToolRegistry.execute_mocked()` é o único caminho de execução de
ferramenta — não existe (e não vai existir sem uma spec/ADR dedicado e revisão de
segurança) um caminho de execução real dentro do `AgentRunner`. O resultado de
cada tool call mockada vem de um stub definido no próprio `EvaluationCase`/teste,
nunca de uma chamada de rede ou banco real.

Casos com `requires_approval: true` são tratados de forma ainda mais conservadora:
o runner nem chega a mockar a execução — ele para e marca
`blocked_pending_approval: true`, simulando o comportamento esperado de um agente
que pede confirmação humana antes de agir.

## Consequências
- Datasets de avaliação nunca podem alterar dados reais, mesmo por engano.
- Testar um `ClaudeProviderAdapter` real (fase futura) ainda é seguro, porque o
  isolamento está na camada de `ToolRegistry`, não no provider.
- Quando ferramentas reais forem necessárias (ex. avaliação de integração real
  em ambiente controlado), isso exige uma nova decisão arquitetural explícita —
  não é um efeito colateral acidental de trocar o provider.
