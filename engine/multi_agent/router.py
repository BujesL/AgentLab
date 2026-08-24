import json
from typing import Protocol

import requests

from engine.json_parsing import parse_json_object

ROUTER_PROMPT_TEMPLATE = """Você é um roteador técnico de um sistema de atendimento com \
vários agentes especialistas. Dado o pedido do usuário, escolha qual especialista deve \
atender, entre os disponíveis.

Especialistas disponíveis: {specialists}

Pedido do usuário: "{input}"

Responda APENAS com um JSON no formato exato:
{{"agent": "<nome de um dos especialistas disponíveis>", "reasoning": "explicação breve"}}
"""


class Router(Protocol):
    def route(self, input: str, specialists: list[str]) -> str:
        """Return the name of the specialist that should handle `input`.

        The returned name is not guaranteed to be a member of `specialists` —
        callers (e.g. MultiAgentRunner) must validate it before dispatching.
        """
        ...


class RoutingError(Exception):
    """Raised when the router's raw output can't be interpreted at all."""


class LLMRouter:
    """Routes by asking an LLM to pick a specialist name, same closed-prompt
    pattern as engine.evaluators.llm_judge — not free-form text.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 180,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def route(self, input: str, specialists: list[str]) -> str:
        prompt = ROUTER_PROMPT_TEMPLATE.format(specialists=specialists, input=input)

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "seed": 42},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()["response"]

        try:
            decision = parse_json_object(raw)
            return str(decision["agent"])
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise RoutingError(f"failed to parse router output: {raw[:200]!r}") from exc
