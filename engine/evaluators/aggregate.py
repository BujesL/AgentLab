from engine.evaluators.answer_accuracy import evaluate_answer_accuracy
from engine.evaluators.groundedness import evaluate_groundedness
from engine.evaluators.handoff import evaluate_handoff
from engine.evaluators.llm_judge import evaluate_answer_llm_judge
from engine.evaluators.models import EvaluationResult
from engine.evaluators.prompt_leak import evaluate_prompt_leak
from engine.evaluators.safety import evaluate_safety
from engine.evaluators.tool_arguments import evaluate_tool_arguments
from engine.evaluators.tool_selection import evaluate_tool_selection
from engine.models import EvaluationCase
from engine.multi_agent.models import AgentSpec
from engine.runner import RunResult
from engine.tools.registry import ToolRegistry


def evaluate_case(
    case: EvaluationCase,
    run_result: RunResult,
    llm_judge_model: str | None = None,
    groundedness_model: str | None = None,
    registry: ToolRegistry | None = None,
    specialists: dict[str, AgentSpec] | None = None,
    system_prompt: str | None = None,
) -> EvaluationResult:
    evaluations = [
        evaluate_tool_selection(case, run_result),
        evaluate_tool_arguments(case, run_result),
    ]
    if llm_judge_model:
        # Substitui (não soma) a comparação exata de answer_accuracy: com AND estrito,
        # somar os dois só poderia derrubar passed, nunca elevá-lo quando a comparação
        # exata já reprovou por diferença de formato (texto livre vs. estruturado).
        # Ver docs/specs/llm-judge/tasks.md para o histórico dessa decisão.
        evaluations.append(evaluate_answer_llm_judge(case, run_result, model=llm_judge_model))
    else:
        evaluations.append(evaluate_answer_accuracy(case, run_result))

    if groundedness_model:
        # Ortogonal a tool_selection/tool_arguments/answer_accuracy: mede fundamentação
        # no contexto, não corretude de tool-calling — por isso soma em vez de substituir.
        # Ver docs/specs/groundedness/spec.md.
        evaluations.append(
            evaluate_groundedness(case, run_result, model=groundedness_model)
        )

    if registry is not None:
        # Deterministic, free — always included when a registry is available (no CLI
        # flag needed, unlike llm_judge/groundedness which cost a network call).
        # Ortogonal aos demais: mede tentativa de ação perigosa, não corretude de
        # conteúdo. Ver docs/specs/safety/spec.md.
        evaluations.append(evaluate_safety(case, run_result, registry))

    # Deterministic, free, trivially passes when case.expected_agent is None —
    # same opt-in-silent pattern as Groundedness. Always included so single-agent
    # cases (the overwhelming majority of existing datasets) are unaffected.
    # See docs/specs/multi-agent-eval/spec.md.
    evaluations.append(evaluate_handoff(case, run_result, specialists))

    # Deterministic, free, trivially passes when no system_prompt was used —
    # same pattern as handoff. Orthogonal to safety (tool attempts) and to
    # answer_accuracy/llm_judge (content correctness): this only asks whether
    # the prompt itself leaked. See docs/specs/advanced-safety/spec.md.
    evaluations.append(evaluate_prompt_leak(case, run_result, system_prompt))

    scores = {e.metric: e.score for e in evaluations}
    passed = all(e.passed for e in evaluations)
    failure_reason = (
        "; ".join(e.reason for e in evaluations if not e.passed and e.reason) or None
    )

    return EvaluationResult(
        case_id=case.id,
        scores=scores,
        passed=passed,
        failure_reason=failure_reason,
    )
