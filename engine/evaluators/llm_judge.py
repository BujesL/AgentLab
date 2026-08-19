import json
import re

import requests

from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.runner import RunResult

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


def _parse_judge_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def evaluate_answer_llm_judge(
    case: EvaluationCase,
    run_result: RunResult,
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
) -> EvalScore:
    actual_text = (run_result.final_answer or {}).get("text", "")
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        input=case.input,
        expected_behavior=case.expected_behavior,
        expected_answer=case.expected_answer,
        actual_text=actual_text,
    )

    response = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
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
