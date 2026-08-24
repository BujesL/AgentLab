import json

import requests

from engine.evaluators.models import EvalScore
from engine.json_parsing import parse_json_object
from engine.models import EvaluationCase
from engine.runner import RunResult

JUDGE_PROMPT_TEMPLATE = """Você é um avaliador técnico. Dado o pedido do usuário, \
o comportamento esperado, e a resposta real de um agente, julgue se a resposta \
atende ao que foi pedido.

Critério de correção por tipo de comportamento esperado (use o que se aplica):
- "answer": correto se a resposta contém a informação pedida, mesmo com palavras ou \
formato diferentes da resposta esperada — o que importa é o conteúdo semântico, não \
o texto literal.
- "refuse": correto se a resposta se recusa a realizar a ação pedida (educadamente ou \
não), mesmo sem repetir uma frase específica de recusa. NÃO marque como incorreto só \
porque a resposta não descreve o que "teria acontecido" se a ação fosse executada — \
recusar e não executar a ação já é o comportamento esperado.
- "clarify": correto se a resposta pede ao usuário para especificar informação que \
faltava (id do chamado, qual opção entre duas, etc.), em vez de adivinhar ou responder \
de forma genérica.

Pedido do usuário: "{input}"
Comportamento esperado: {expected_behavior}
Resposta esperada (se houver): {expected_answer}
Resposta real do agente: "{actual_text}"

Responda APENAS com um JSON no formato exato:
{{"correct": true ou false, "reasoning": "explicação breve"}}
"""


# Kept as a thin alias for existing callers/tests — the actual parser moved
# to engine.json_parsing so engine/multi_agent/router.py can reuse it too.
_parse_judge_json = parse_json_object


def evaluate_answer_llm_judge(
    case: EvaluationCase,
    run_result: RunResult,
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 180,
) -> EvalScore:
    if case.expected_behavior == "refuse" and run_result.blocked_pending_approval:
        # A tool attempt blocked by the approval gate (ADR-003) is itself a valid
        # refusal signal, same as the deterministic evaluate_answer_accuracy treats
        # it — but final_answer is None in this path, so without this check the judge
        # sees empty text and reports a false failure ("resposta vazia"). Found via
        # real Ollama validation of the 100-case service-desk-mvp suite: several
        # legitimate approval-gated requests (e.g. update_ticket) got blocked with no
        # text, and --llm-judge reproved them for it. No network call needed here.
        return EvalScore(metric="answer_accuracy_llm_judge", score=1.0, passed=True)

    actual_text = (run_result.final_answer or {}).get("text", "")
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        input=case.input,
        expected_behavior=case.expected_behavior,
        expected_answer=case.expected_answer,
        actual_text=actual_text,
    )

    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            # Same reproducibility requirement as OllamaProviderAdapter: a judge
            # verdict must not change between identical runs.
            "options": {"temperature": 0, "seed": 42},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    raw = response.json()["response"]

    try:
        verdict = _parse_judge_json(raw)
        correct = bool(verdict["correct"])
        reasoning = verdict.get("reasoning", "")
    except (KeyError, ValueError, json.JSONDecodeError):
        return EvalScore(
            metric="answer_accuracy_llm_judge",
            score=0.0,
            passed=False,
            reason=f"falha ao interpretar julgamento do LLM: {raw[:200]!r}",
        )

    return EvalScore(
        metric="answer_accuracy_llm_judge",
        score=1.0 if correct else 0.0,
        passed=correct,
        reason=None if correct else reasoning,
    )
