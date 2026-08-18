# Spec: CLI

Status: **em desenvolvimento (MVP)**

## Problema

Tudo que construímos (dataset, runner, trace, evaluators, persistência) só é
acionável hoje via código Python direto em testes. O documento-base (seção 21)
prevê uma CLI (`agentlab ...`) como interface principal do MVP — o dashboard
só chega na Fase V1.

## Resultado esperado

Uma CLI com três comandos cobrindo o ciclo completo do MVP:

1. `agentlab dataset validate <path>` — valida um dataset (já especificado,
   reaproveita `engine.datasets.validate_dataset`).
2. `agentlab evaluate <dataset_path> --scripts <scripts.json>` — roda o
   pipeline inteiro: carrega dataset → executa `AgentRunner` por caso →
   constrói `Trace` → avalia com `evaluate_case` → persiste (se
   `DATABASE_URL` definida) → imprime relatório agregado.
3. `agentlab trace show <trace_id>` — busca um trace persistido e mostra a
   visualização estilo seção 15 (Trace Viewer em texto).

## Limitação honesta: não existe Provider real ainda

Não há `ClaudeProviderAdapter` implementado (adiado desde a spec de Agent
Runner). Para a CLI ser útil e testável agora, `evaluate` usa
`MockProviderAdapter`, roteirizado por um arquivo `scripts.json` fornecido
pelo usuário (mapeia `case_id -> lista de passos`). Isso **não é uma avaliação
real de um agente de IA** — é o pipeline de avaliação rodando ponta a ponta
contra um duplo de teste determinístico, útil para validar a ferramenta e
para desenvolvimento. Quando um provider real existir, o comando `evaluate`
ganha uma flag `--provider claude` (ou similar) sem mudar a interface do
usuário — é só trocar a implementação por trás.

## Escopo

### Dentro do escopo (MVP)

- Os três comandos acima.
- Persistência opcional (`--no-persist` desliga; sem `DATABASE_URL` no
  ambiente, a persistência é pulada com aviso, não erro fatal — permite rodar
  `evaluate` só para ver o relatório, sem precisar de banco).
- Relatório agregado no formato da seção 25 (contagem, accuracy %, custo
  médio, latência média).
- Exit code 0 se todos os casos passaram, 1 se algum falhou — ponto de
  integração futuro com CI/quality gate (Fase V1.5), já correto desde agora.

### Fora do escopo (fases futuras)

- `agentlab compare`, `agentlab regression run`, `agentlab quality-gate` —
  dependem de Experiment Manager e Regression Testing (specs futuras).
- Provider real (Claude) — spec futura.
- Empacotamento como executável instalável (`pip install -e .` com entry
  point) — por ora roda via `python -m engine.cli`.

## Critérios de aceitação

- [ ] `dataset validate` com dataset válido retorna exit code 0 e imprime
      confirmação.
- [ ] `dataset validate` com dataset inválido retorna exit code 1 e imprime
      os erros específicos (não genérico).
- [ ] `evaluate` com `--no-persist` roda o pipeline completo e imprime
      relatório agregado sem precisar de banco.
- [ ] `evaluate` retorna exit code 1 se qualquer caso falhar, 0 se todos
      passarem.
- [ ] `evaluate` reporta claramente um caso do dataset sem script
      correspondente em `scripts.json` (não trava a execução dos demais).
- [ ] `trace show <id>` inexistente retorna mensagem clara de "não
      encontrado", não uma stack trace.
