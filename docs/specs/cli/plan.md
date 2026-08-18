# Plan: CLI

## Biblioteca

`argparse` (stdlib) — suficiente para 3 comandos/subcomandos, sem dependência
nova. Decisão adiada desde `docs/specs/evaluation-engine/plan.md`, resolvida
aqui.

## Formato do arquivo de scripts (`scripts.json`)

```json
{
  "SD-001": [
    {"kind": "tool_call_request", "tool_name": "get_tickets", "arguments": {"priority": "urgent"}},
    {"kind": "final_answer", "answer": {"count": 4}}
  ],
  "SD-004": [
    {"kind": "final_answer", "answer": {"text": "24/7"}}
  ]
}
```

`engine/cli_scripts.py::load_scripts(path) -> dict[str, list[ProviderStep]]`
converte cada dict em `ToolCallRequest`/`FinalAnswer` (por `kind`).

## Estrutura de comandos (`engine/cli.py`)

```
def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)  # cada subcomando define seu handler

def build_parser():
    # agentlab dataset validate <path>
    # agentlab evaluate <dataset_path> --scripts <path> [--model mock] [--no-persist]
    # agentlab trace show <trace_id>
```

## Handler `dataset validate`

Reaproveita `engine.datasets.validate_dataset`. Imprime `OK` + contagem de
casos se válido (exit 0); imprime cada erro em uma linha e retorna exit 1 se
inválido.

## Handler `evaluate`

```
def handle_evaluate(args) -> int:
    dataset = load_dataset(args.dataset_path)
    scripts = load_scripts(args.scripts)
    registry = build_default_registry()  # tools mockadas conhecidas do dataset

    conn = None
    if not args.no_persist and "DATABASE_URL" in os.environ:
        conn = get_connection()
    elif not args.no_persist:
        print("aviso: DATABASE_URL não definida, pulando persistência")

    results = []
    for case in dataset.cases:
        if case.id not in scripts:
            print(f"AVISO: sem script para {case.id}, pulando")
            continue
        provider = MockProviderAdapter(scripts[case.id])
        run_result = AgentRunner().run(case, provider, registry)
        trace = build_trace(run_result, model=args.model)
        evaluation = evaluate_case(case, run_result)
        if conn:
            save_trace(conn, trace)
            save_evaluation_result(conn, evaluation, trace_id=trace.id)
        results.append((case, evaluation, trace))
        print(f"{case.id}: {'PASS' if evaluation.passed else 'FAIL'}"
              + (f" — {evaluation.failure_reason}" if not evaluation.passed else ""))

    print_summary(results)  # seção 25: contagem, accuracy%, custo médio, latência média
    return 0 if all(e.passed for _, e, _ in results) else 1
```

`build_default_registry()` é montado a partir das `ToolSpec`s conhecidas do
dataset MVP (`get_tickets`, `update_ticket`, `delete_all_tickets` etc.) com
stubs fixos — suficiente para o dataset de exemplo; documentado como
limitação (um dataset novo precisaria de tools registradas manualmente por
ora, sem um mecanismo de tool registry por dataset ainda — fica para V1).

## Handler `trace show`

Conecta no banco, busca via `get_trace`, imprime no formato:
```
Evaluation <trace_id>
│
├── INPUT
│     '<input>'
├── TOOL CALL / TOOL RESULT / FINAL ANSWER (por evento, na ordem)
└── METRICS
      duration=<duration_ms>ms tokens=<token_usage> cost=$<cost>
```
Se não encontrado, imprime `"trace <id> não encontrado"` e retorna exit 1.

## Passos de implementação

1. `engine/cli_scripts.py` — `load_scripts`.
2. `engine/cli_registry.py` — `build_default_registry` (tools do dataset MVP).
3. `engine/cli.py` — `build_parser`, `main`, os três handlers.
4. `datasets/service-desk-mvp/scripts.json` — roteiro para o dataset MVP
   (12 casos), permitindo `evaluate` rodar de ponta a ponta sobre dados reais
   do projeto.
5. `tests/unit/test_cli.py` — chama `main(argv)` diretamente (sem subprocess),
   captura stdout via `capsys`, cobre os 6 critérios de aceitação usando
   `--no-persist` para não depender de banco nos testes unitários.
6. Rodar suíte completa.

## Fora deste plano

Empacotamento (`pyproject.toml` com entry point `agentlab`) — cosmético,
pode vir depois sem afetar a lógica.
