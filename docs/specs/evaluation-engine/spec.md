# Spec: Evaluation Case + Dataset

Status: **em desenvolvimento (MVP)**

## Problema

Precisamos de uma forma versionável e validável de descrever "o que o agente deve
fazer dado um input" — incluindo qual ferramenta é esperada, com quais argumentos,
e qual resultado é considerado correto. Sem isso, não há base determinística para
nenhuma métrica (Answer Accuracy, Tool Selection, Tool Argument Accuracy).

## Resultado esperado

1. Um schema JSON formal para `EvaluationCase`.
2. Um schema para `Dataset` (coleção de `EvaluationCase` + metadados de versão).
3. Validação executável (`agentlab dataset validate <nome>`, seção 21 do
   documento-base) que rejeita casos malformados antes de qualquer execução.
4. Um dataset inicial reduzido (10-15 casos) cobrindo as categorias da seção 24 do
   documento-base, para validar o pipeline ponta a ponta no MVP.

## Escopo

### Dentro do escopo (MVP)

- Schema de `EvaluationCase` com: input, expected_tools, expected_arguments,
  expected_answer, expected_behavior, requires_approval.
- Schema de `Dataset`: id, name, version, description, cases[].
- Validação de schema (tipos, campos obrigatórios, formato de IDs).
- Dataset inicial de exemplo em `datasets/service-desk-mvp/`.

### Fora do escopo (fases futuras)

- Categorização automática/tagging avançado de casos — Fase V1.
- Versionamento semântico de datasets com diffing — Fase V1.5 (junto de Regression
  Testing).
- Dataset completo de 100 casos — expandir após o pipeline MVP estar validado.

## Critérios de aceitação

- [ ] Um `EvaluationCase` válido conforme o schema é aceito pelo validador.
- [ ] Um `EvaluationCase` com campo obrigatório faltando é rejeitado com mensagem
      de erro clara (qual campo, por quê).
- [ ] Um `Dataset` com um caso inválido falha a validação do dataset inteiro
      (fail explicitamente — princípio da seção 3 do documento-base).
- [ ] `expected_tools` vazio é válido (caso de resposta direta sem tool call).
- [ ] `expected_behavior: "refuse"` é suportado (casos de solicitação proibida,
      seção 24).
- [ ] Dataset inicial de exemplo passa na validação.

## Categorias de caso cobertas no dataset inicial (subconjunto da seção 24)

1. Consulta informacional simples (sem tool call).
2. Chamada de ferramenta com argumentos corretos.
3. Chamada de ferramenta com argumentos incorretos esperados como erro do agente.
4. Caso que exige aprovação (`requires_approval: true`).
5. Prompt injection (o agente deve ignorar instrução maliciosa embutida no input).
6. Solicitação proibida (`expected_behavior: "refuse"`).
7. Caso ambíguo (múltiplas interpretações válidas — sem resposta única).
8. Caso sem dados suficientes (o agente deve pedir esclarecimento, não inventar).

Não cobrimos todas as 8 categorias com o mesmo peso no MVP — o objetivo é ter
pelo menos 1-2 exemplos de cada para validar que o schema suporta todos os casos,
não medir cobertura estatística ainda.
