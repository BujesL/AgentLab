from engine.evaluators.llm_judge import _parse_judge_json
from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.runner import RunResult

import requests

GROUNDEDNESS_PROMPT_TEMPLATE = """Você é um avaliador técnico de sistemas RAG. Dado um \
contexto fornecido a um agente e a resposta real que ele deu, julgue se a resposta é \
inteiramente fundamentada nesse contexto.

Regras de julgamento:
- Marque `grounded=true` se todo fato afirmado na resposta está presente ou é uma \
inferência direta do contexto — mesmo com palavras diferentes.
- Marque `grounded=false` se a resposta afirma algo que NÃO está no contexto \
(alucinação), mesmo que a afirmação seja verdadeira no mundo real — o que importa \
aqui é a origem da informação, não se ela é factualmente correta.
- Se o contexto não contém a resposta e o agente disse que não sabe ou não tem essa \
informação, marque `grounded=true` — recusar por falta de informação no contexto é o \
comportamento correto, não uma alucinação.

Contexto fornecido:
{context}

Resposta real do agente: "{actual_text}"

Responda APENAS com um JSON no formato exato:
{{"grounded": true ou false, "reasoning": "explicação breve"}}
"""


def evaluate_groundedness(
    case: EvaluationCase,
    run_result: RunResult,
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 180,
) -> EvalScore:
    if not case.context:
        return EvalScore(
            metric="groundedness",
            score=1.0,
            passed=True,
            reason="caso sem context associado — métrica não aplicável",
        )

    actual_text = (run_result.final_answer or {}).get("text", "")
    prompt = GROUNDEDNESS_PROMPT_TEMPLATE.format(
        context="\n".join(f"- {passage}" for passage in case.context),
        actual_text=actual_text,
    )

    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "seed": 42},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    raw = response.json()["response"]

    try:
        verdict = _parse_judge_json(raw)
        grounded = bool(verdict["grounded"])
        reasoning = verdict.get("reasoning", "")
    except (KeyError, ValueError) as exc:
        return EvalScore(
            metric="groundedness",
            score=0.0,
            passed=False,
            reason=f"falha ao interpretar julgamento do LLM: {raw[:200]!r} ({exc})",
        )

    return EvalScore(
        metric="groundedness",
        score=1.0 if grounded else 0.0,
        passed=grounded,
        reason=None if grounded else reasoning,
    )
