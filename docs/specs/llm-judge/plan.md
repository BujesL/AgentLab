# Plan: LLM-as-a-Judge

## `engine/evaluators/llm_judge.py`

```python
JUDGE_PROMPT_TEMPLATE = """Você é um avaliador técnico. Dado o pedido do usuário, \
o comportamento esperado, e a resposta real de um agente, julgue se a resposta \
atende ao que foi pedido.

Pedido do usuário: "{input}"
Comportamento esperado: {expected_behavior}
Resposta esperada (se houver): {expected_answer}
Resposta real do agente: "{actual_text}"

Responda APENAS com um JSON no formato exato:
{{"correct": true ou false, "reasoning": "explicação breve"}}
"""

def evaluate_answer_llm_judge(case, run_result, model="llama3.2", base_url="http://localhost:11434") -> EvalScore:
    actual_text = (run_result.final_answer or {}).get("text", "")
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        input=case.input,
        expected_behavior=case.expected_behavior,
        expected_answer=case.expected_answer,
        actual_text=actual_text,
    )
    response = requests.post(f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
        timeout=60)
    response.raise_for_status()
    raw = response.json()["response"]

    try:
        verdict = _parse_judge_json(raw)
        correct = bool(verdict["correct"])
        reasoning = verdict.get("reasoning", "")
    except (KeyError, ValueError, json.JSONDecodeError):
        return EvalScore(metric="answer_accuracy_llm_judge", score=0.0, passed=False,
                          reason=f"falha ao interpretar julgamento do LLM: {raw[:200]!r}")

    return EvalScore(
        metric="answer_accuracy_llm_judge",
        score=1.0 if correct else 0.0,
        passed=correct,
        reason=reasoning if not correct else None,
    )
```

`format: "json"` é um recurso do Ollama que força saída JSON válida — reduz
(não elimina) a chance de resposta mal formatada; ainda assim mantemos o
parsing defensivo com fallback claro.

`_parse_judge_json(raw)` — tenta `json.loads(raw)` direto; se falhar,
extrai o primeiro bloco `{...}` da string (tolerância a texto extra ao
redor, ex. respostas de modelos que ignoram `format: json` parcialmente).

## Integração com `evaluate_case`

`engine/evaluators/aggregate.py::evaluate_case` ganha parâmetro opcional
`llm_judge_model: str | None = None`:

```python
def evaluate_case(case, run_result, llm_judge_model=None) -> EvaluationResult:
    evaluations = [
        evaluate_tool_selection(case, run_result),
        evaluate_tool_arguments(case, run_result),
        evaluate_answer_accuracy(case, run_result),
    ]
    if llm_judge_model:
        evaluations.append(evaluate_answer_llm_judge(case, run_result, model=llm_judge_model))
    ...
```

Quando `llm_judge_model` é `None` (padrão), comportamento idêntico ao que já
existia — retrocompatível com todos os testes/specs anteriores.

## CLI

`evaluate --llm-judge [--judge-model <nome>]` (default do judge-model =
mesmo `--model` usado pelo provider, se não especificado). Passa
`llm_judge_model=args.judge_model or args.model` para `evaluate_case`
quando `--llm-judge` está presente.

## Passos de implementação

1. `engine/evaluators/llm_judge.py`.
2. Atualizar `engine/evaluators/aggregate.py`.
3. Atualizar `engine/cli.py` (`--llm-judge`, `--judge-model`).
4. `tests/unit/test_llm_judge_parsing.py` — só a lógica de parsing
   (`_parse_judge_json`), sem chamar Ollama de verdade (mantém a suíte
   unitária rápida e sem dependência externa).
5. Rodar manualmente `evaluate --provider ollama --llm-judge` contra o
   dataset MVP, comparar taxa de aprovação com/sem o juiz.

## Fora deste plano

Calibração formal, ensemble de juízes — ver "fora do escopo" em spec.md.
