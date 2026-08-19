# Spec: OllamaProviderAdapter (primeiro Provider real)

Status: **em desenvolvimento (V2)**

## Problema

Desde a spec de Agent Runner (MVP), todo `ProviderAdapter` usado foi
`MockProviderAdapter` — um duplo de teste scriptado, nunca um LLM de
verdade raciocinando. Isso foi deliberadamente adiado ("fora do escopo",
`docs/specs/agent-runner/spec.md`) até existir um motivo real para pagar
esse custo de implementação. A V2 (LLM-as-a-Judge, Groundedness) é esse
motivo: precisamos de um LLM real para julgar semanticamente, e faz sentido
usar o mesmo LLM como Provider real, gratuitamente, via Ollama local — ver
decisão de "estratégia gratuita" desta sessão.

## Resultado esperado

1. `OllamaProviderAdapter(model: str)` implementando `ProviderAdapter` —
   chama `http://localhost:11434/api/chat` de verdade, com tool calling.
2. Um `EvaluationCase` real do dataset MVP rodado contra esse provider (não
   scriptado) produz um `RunResult`/`Trace` genuínos.

## Descoberta esperada e documentada de antemão: mismatch de formato

Os `EvaluationCase.expected_answer` do MVP são dicts estruturados (ex.
`{"count": 4}`), pensados para comparação exata (Answer Accuracy
determinística, seção 12). Um LLM real responde em linguagem natural
("Existem 4 chamados atrasados."), não um dict. Isso significa:

- `evaluate_answer_accuracy` (comparação exata) **vai falhar** sistemática e
  corretamente contra um provider real, mesmo quando a resposta está
  semanticamente certa — não é um bug, é a limitação conhecida e esperada
  de comparação determinística contra texto livre.
- É exatamente o motivo de existir LLM-as-a-Judge (spec seguinte): compara
  semanticamente "Existem 4 chamados atrasados" com `{"count": 4}` /
  contexto do caso, em vez de igualdade estrutural.

Este documento **antecipa** essa descoberta em vez de tratá-la como bug
depois — está registrada aqui antes de rodar qualquer coisa.

## Escopo

### Dentro do escopo (V2)

- `engine/providers/ollama.py::OllamaProviderAdapter`.
- Conversão de `ToolSpec` → formato de tools do Ollama (`/api/chat`
  `tools` param, compatível com o formato usado por modelos com function
  calling, ex. `llama3.2`).
- `FinalAnswer.answer` para um provider real é sempre
  `{"text": <conteúdo bruto do LLM>}` — formato uniforme, nunca tenta
  adivinhar/parsear a estrutura esperada (isso é responsabilidade do
  avaliador, não do adapter).
- Suporte a system prompt (usa o conteúdo de `--prompt-file` já existente,
  spec de Prompt Versioning).
- CLI: `evaluate --provider ollama --model <nome-do-modelo-ollama>` (hoje
  `--model` é só um rótulo de custo; passa a também selecionar o provider
  real quando `--provider ollama`).

### Fora do escopo (fases futuras)

- Providers reais de outros fabricantes (Claude API, OpenAI) — mesma
  interface, adapter separado, spec própria se/quando necessário.
- Retry/backoff sofisticado para chamadas Ollama — timeout simples é
  suficiente para uso local.

## Critérios de aceitação

- [ ] `OllamaProviderAdapter.step()` faz uma chamada HTTP real ao Ollama
      local e retorna `ToolCallRequest` ou `FinalAnswer` corretamente
      parseados da resposta.
- [ ] Uma tool disponível no registro é oferecida ao modelo no formato
      correto; se o modelo decidir chamá-la, o `AgentRunner` executa (mockada,
      ADR-003) e devolve o resultado ao modelo no próximo turno.
- [ ] Rodar `SD-004` (pergunta sem necessidade de tool) contra o Ollama
      real produz uma resposta em texto livre, capturada em
      `final_answer.text`.
- [ ] Documentado e observado na prática: `evaluate_answer_accuracy`
      falha para esse caso mesmo com resposta semanticamente correta
      (evidência do mismatch antecipado acima).
