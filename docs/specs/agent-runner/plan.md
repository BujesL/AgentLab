# Plan: Agent Runner + Provider Adapter

## Modelos e interfaces (Python)

```
ToolSpec (Pydantic)
├── name: str
├── description: str
├── input_schema: dict          # JSON Schema do input
├── output_schema: dict | None
├── risk_level: Literal["low", "medium", "high"] = "low"
├── requires_approval: bool = False
└── enabled_for_evaluation: bool = True

ToolCall (Pydantic)
├── tool_name: str
├── arguments: dict
└── result: dict | None          # None se bloqueado por aprovação

RunResult (Pydantic)
├── case_id: str
├── tool_calls: list[ToolCall]
├── final_answer: dict | None
├── blocked_pending_approval: bool = False
└── raw_events: list[dict]       # payload cru por passo, insumo do Trace Model

ProviderAdapter (ABC, engine/providers/base.py)
└── def step(self, input: str, tools: list[ToolSpec], history: list[dict]) -> ProviderStep
    # ProviderStep = tool_call_request | final_answer (union simples)

ToolRegistry (engine/tools/registry.py)
├── register(tool: ToolSpec)
├── get(name: str) -> ToolSpec
└── execute_mocked(name: str, arguments: dict, stub_result: dict | None) -> dict
```

## AgentRunner — algoritmo

```
def run(case, provider, registry, max_iterations=5) -> RunResult:
    history = []
    tool_calls = []
    for _ in range(max_iterations):
        step = provider.step(case.input, registry.enabled_tools(), history)
        if step.kind == "final_answer":
            return RunResult(case_id=case.id, tool_calls=tool_calls,
                              final_answer=step.answer, raw_events=history)
        # step.kind == "tool_call_request"
        tool = registry.get(step.tool_name)
        if tool.requires_approval:
            return RunResult(case_id=case.id, tool_calls=tool_calls,
                              blocked_pending_approval=True, raw_events=history)
        result = registry.execute_mocked(step.tool_name, step.arguments)
        tool_calls.append(ToolCall(tool_name=step.tool_name,
                                    arguments=step.arguments, result=result))
        history.append({"type": "tool_result", "tool": step.tool_name, "result": result})
    raise RuntimeError(f"max_iterations exceeded for case {case.id}")
```

Ferramenta é sempre mockada no MVP (`execute_mocked`) — nunca há execução real,
alinhado ao ADR-005 (a ser registrado nesta etapa).

## MockProviderAdapter — como decide o que responder

Para permitir testes determinísticos sem LLM real, o `MockProviderAdapter` recebe
um mapa `case_id -> list[ProviderStep]` na construção (roteiro fixo do que
"responder" passo a passo). Isso não simula um LLM de verdade — é um duplo de
teste para validar o `AgentRunner` e, depois, o Evaluation Engine, isoladamente
da variabilidade de um LLM real. A implementação de um adapter real (Claude) fica
para uma iteração seguinte desta mesma spec (ver spec.md, "fora do escopo").

## Passos de implementação

1. `engine/providers/base.py` — `ProviderAdapter` (ABC), `ProviderStep`,
   `ToolCallRequest`, `FinalAnswer`.
2. `engine/tools/models.py` — `ToolSpec`, `ToolCall`.
3. `engine/tools/registry.py` — `ToolRegistry`.
4. `engine/runner.py` — `RunResult`, `AgentRunner`.
5. `engine/providers/mock.py` — `MockProviderAdapter`.
6. `docs/architecture/decisions/ADR-003-ferramentas-mockadas-por-padrao.md`.
7. `tests/unit/test_runner.py` — cobre os 6 critérios de aceitação da spec,
   usando os casos SD-001 (tool call simples), SD-003/SD-011 (requires_approval),
   SD-004 (sem tool).
8. Rodar testes, confirmar passagem com evidência real.

## Fora deste plano

Trace Model formal (próxima spec) — aqui só produzimos `raw_events`/`RunResult`
como insumo bruto. Evaluation Engine (Answer Accuracy/Tool Selection) — spec
seguinte, consome `RunResult` + `EvaluationCase` esperado.
