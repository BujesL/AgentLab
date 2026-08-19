# Plan: OllamaProviderAdapter

## API do Ollama usada

`POST http://localhost:11434/api/chat` (não streaming, `"stream": false"`),
payload:

```json
{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "<system prompt, se houver>"},
    {"role": "user", "content": "<case.input>"},
    {"role": "tool", "content": "<resultado da tool, se houver, no próximo turno>"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_tickets",
        "description": "...",
        "parameters": { "type": "object", "properties": {...} }
      }
    }
  ]
}
```

Resposta relevante: `message.tool_calls` (lista, cada item com
`function.name`/`function.arguments`) ou `message.content` (texto).

## Conversão `ToolSpec` → tool do Ollama

```python
def _to_ollama_tool(tool: ToolSpec) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }
```

## `OllamaProviderAdapter.step()`

```python
class OllamaProviderAdapter:
    def __init__(self, model: str, system_prompt: str | None = None, base_url="http://localhost:11434"):
        ...

    def step(self, input, tools, history) -> ProviderStep:
        messages = self._build_messages(input, history)  # a partir do histórico já visto
        response = requests.post(f"{self.base_url}/api/chat", json={
            "model": self.model, "messages": messages,
            "tools": [_to_ollama_tool(t) for t in tools], "stream": False,
        }, timeout=60)
        response.raise_for_status()
        message = response.json()["message"]

        if message.get("tool_calls"):
            call = message["tool_calls"][0]
            return ToolCallRequest(tool_name=call["function"]["name"],
                                    arguments=call["function"]["arguments"])
        return FinalAnswer(answer={"text": message.get("content", "")})
```

`_build_messages` reconstrói a conversa a partir de `history` (já produzido
pelo `AgentRunner`, reaproveitando os eventos `tool_call_request`/
`tool_result` como mensagens `assistant`/`tool` do Ollama) — não precisa de
estado próprio no adapter, `history` já é a fonte de verdade (mesmo design
que `MockProviderAdapter` recebe, mas aqui é usado de verdade em vez de
ignorado).

## Passos de implementação

1. Adicionar `requests` a `engine/requirements.txt`.
2. `engine/providers/ollama.py::OllamaProviderAdapter`.
3. Atualizar `engine/cli.py` — `--provider {mock,ollama}`, quando `ollama`
   usa `OllamaProviderAdapter(model=args.model, system_prompt=<conteúdo de
   --prompt-file, se houver>)` em vez de `MockProviderAdapter` (que exige
   `--scripts`; com `--provider ollama`, `--scripts` deixa de ser
   obrigatório).
4. Rodar manualmente (não é teste automatizado — depende de Ollama local
   rodando, então fica documentado como validação manual, não parte da
   suíte de CI) contra 2-3 casos do dataset MVP, capturar o
   `RunResult`/`Trace` real.
5. Documentar a descoberta do mismatch de formato (spec.md) com exemplo real.

## Fora deste plano

Testes automatizados que dependem de Ollama rodando não entram na suíte
padrão (`tests/unit`, `tests/integration`) — ficam como script de validação
manual (`scripts/validate_ollama_provider.py`), já que CI não tem Ollama
disponível (V2 é sobre capacidade local, não sobre CI aqui).
