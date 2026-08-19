# Spec: LLM-as-a-Judge

Status: **em desenvolvimento (V2)**

## Problema

A spec de `OllamaProviderAdapter` confirmou na prática: um provider real
responde em texto livre, e `evaluate_answer_accuracy` (comparação exata)
falha sistematicamente contra isso — 0/12 no dataset MVP, mesmo quando a
resposta do modelo era semanticamente razoável. O documento-base já previa
essa necessidade (seção 12): "Conteúdo semântico → LLM-as-a-Judge
calibrado".

## Resultado esperado

1. Um avaliador `evaluate_answer_llm_judge(case, run_result, model) ->
   EvalScore` que usa um LLM (via Ollama, mesma decisão de "estratégia
   gratuita") para julgar semanticamente se a resposta em texto livre
   satisfaz a intenção do caso.

   **Revisão de design (pós-implementação, ver tasks.md)**: a intenção
   original era o juiz ser complementar (somado) ao avaliador determinístico
   de `answer_accuracy`, nunca substituindo-o. Na prática isso se mostrou
   estruturalmente inviável: `evaluate_case` agrega com AND estrito, então
   somar um juiz que aprova a uma comparação exata que já reprovou só pode
   manter ou piorar `passed`, nunca melhorá-lo — o critério de aceitação
   abaixo ("taxa de aprovação > 0%") é matematicamente impossível de
   satisfazer com agregação por soma. Decisão final: quando `--llm-judge`
   está ativo, `evaluate_answer_llm_judge` **substitui**
   `evaluate_answer_accuracy` (não é somado a ele) — `tool_selection` e
   `tool_arguments` continuam deterministas e obrigatórios em ambos os
   casos. Isso preserva "determinismo antes de IA" para chamadas de tool
   (onde exatidão estrutural ainda faz sentido), e usa IA apenas para o
   componente que é genuinamente semântico (texto livre).
2. O prompt de julgamento pede uma saída estruturada (JSON) para que o
   próprio julgamento seja, ele mesmo, parseável deterministicamente — o
   LLM decide o veredito semântico, mas o parsing da resposta do juiz é
   código comum, não mais IA em cima de IA.
3. CLI: `evaluate --llm-judge [--judge-model <nome>]` — opt-in explícito,
   nunca automático (evita custo/latência default; mesmo sendo grátis
   localmente, ainda é ~15-20s por caso).
4. `evaluate_case` ganha um parâmetro opcional para incluir o julgamento do
   LLM nos `scores`, sem quebrar a assinatura/comportamento existente
   quando não usado.

## Formato do prompt de julgamento (decisão de design)

```
Você é um avaliador técnico. Dado o pedido do usuário, o comportamento
esperado, e a resposta real de um agente, julgue se a resposta atende ao
que foi pedido.

Pedido do usuário: "{input}"
Comportamento esperado: {expected_behavior} (answer/refuse/clarify)
Resposta esperada (se houver): {expected_answer}
Resposta real do agente: "{actual_text}"

Responda APENAS com um JSON no formato:
{"correct": true ou false, "reasoning": "explicação breve"}
```

Sem chain-of-thought exposto ao usuário final (ADR-004 já cobre isso para
traces reais; o `reasoning` do juiz é metadado técnico de avaliação, não
raciocínio do agente sendo avaliado — distinção importante, documentada
aqui para não confundir os dois).

## Escopo

### Dentro do escopo (V2)

- `engine/evaluators/llm_judge.py`.
- Parsing robusto de JSON (tolera blocos de código markdown ```json ao
  redor, comum em respostas de LLM).
- Fallback explícito se o parsing falhar: `EvalScore(passed=None-like,
  score=0.0)` com `reason` indicando falha de parsing — nunca assume
  sucesso silenciosamente quando o juiz não respondeu em formato válido
  (fail explicitamente).
- CLI `--llm-judge`.

### Fora do escopo (fases futuras)

- Calibração formal do juiz (comparar julgamentos do LLM com anotação
  humana, medir concordância) — mencionado no documento-base
  ("LLM-as-a-Judge calibrado") mas exige um dataset de referência anotado
  que não existe ainda; registrado como trabalho futuro, não fingido aqui.
- Múltiplos juízes/votação (ensemble) — um juiz simples é suficiente para
  V2; ensemble é uma melhoria de robustez para quando houver evidência de
  que um juiz único erra demais.

## Critérios de aceitação

- [ ] O avaliador retorna `passed=True` para uma resposta real
      semanticamente correta mesmo com formato de texto totalmente
      diferente do `expected_answer` estruturado.
- [ ] O avaliador retorna `passed=False` para uma resposta real
      semanticamente incorreta ou incompleta.
- [ ] Resposta do juiz que não é JSON válido não quebra a avaliação — vira
      `passed=False` com motivo claro de "falha ao interpretar julgamento",
      não uma exceção não tratada.
- [ ] Rodar `evaluate --llm-judge` contra os 12 casos reais do Ollama
      (spec anterior) produz uma taxa de aprovação **maior que 0%** — prova
      concreta de que o juiz resolve o mismatch que a comparação exata não
      resolve.
