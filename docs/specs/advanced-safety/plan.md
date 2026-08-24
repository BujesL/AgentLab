# Plan: Segurança avançada (prompt leak + resource exhaustion)

1. `engine/providers/ollama.py`: adicionar `max_output_tokens: int = 512` ao
   `__init__`, passar como `options.num_predict` em toda chamada a
   `/api/chat`. 512 é generoso o bastante para as respostas reais deste
   dataset (a mais longa observada tem poucas frases) mas finito o
   suficiente pra impedir uma tentativa de reproduzir 100+ linhas de prompt.
2. `engine/evaluators/prompt_leak.py`: `evaluate_prompt_leak(case,
   run_result, system_prompt) -> EvalScore`. Usa
   `difflib.SequenceMatcher.find_longest_match` entre a resposta final e o
   `system_prompt` (normalizando espaço/caixa) — mede o maior trecho
   contíguo em comum, reprova se ultrapassar um limiar de caracteres.
3. `engine/evaluators/aggregate.py`: `evaluate_case` ganha `system_prompt:
   str | None = None`, inclui `prompt_leak` sempre (determinístico, grátis,
   trivial sem `system_prompt`).
4. `engine/cli.py`: `handle_evaluate` já tem `system_prompt` carregado
   (`--prompt-file`) — passar para `evaluate_case`.
   `handle_evaluate_multi_agent`: cada especialista tem seu próprio
   `system_prompt` (via `AgentSpec`) — passar o do especialista que de fato
   respondeu (`case_specialists[chosen_agent]`), não um prompt genérico.
5. Testes unitários: `num_predict` presente no payload da requisição
   (mockando `requests.post`); `evaluate_prompt_leak` trivial sem prompt,
   reprova com vazamento real, não reprova com coincidência curta.
6. Revalidar `SD-076` isolado contra Ollama real com o cap aplicado — a
   evidência real do achado (deve completar sem timeout agora).

## Risco identificado

`num_predict=512` pode cortar uma resposta legítima longa no meio da frase
em algum caso futuro com pedidos mais elaborados que os do dataset atual —
aceito como trade-off deliberado (rede de segurança de infraestrutura >
completude em um caso raro), documentado aqui para reconsiderar se algum
dataset futuro precisar de respostas mais longas.
