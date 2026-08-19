# Spec: Prompt Versioning

Status: **em desenvolvimento (V1.5)**

## Problema

O documento-base (seção 18) prevê comparar `Prompt v1 → Accuracy 89%`,
`Prompt v2 → Accuracy 94%` etc. Hoje não existe nenhum conceito de prompt
versionado — o `MockProviderAdapter` nem usa um prompt real (é scriptado).
Quando um `ProviderAdapter` real existir (Claude), o prompt de sistema usado
precisa ser rastreável por versão/hash, do mesmo jeito que já rastreamos
`AgentVersion`.

## Resultado esperado

1. `PromptVersion` (seção 9: `id, name, version, content_hash`) como entidade
   persistida.
2. `Experiment` ganha `prompt_version_id` opcional (nullable — nem todo
   experimento usa um provider com prompt versionado, ex. o mock).
3. CLI `evaluate` ganha `--prompt-file <path>` opcional: lê o conteúdo do
   arquivo, calcula hash (SHA-256), cria/reusa um `PromptVersion` (por
   `content_hash`), associa ao experimento.
4. Uma comparação simples: dado um `dataset_id` + `agent_version_id`, listar
   accuracy por `prompt_version` (consulta agregada, sem UI nova — a UI já
   existente de comparação, `/compare`, spec anterior, cobre o caso de dois
   experimentos específicos).

## Decisão importante: versionamento é por conteúdo (hash), não manual

Em vez de pedir que o usuário digite "v1", "v2" manualmente (frágil, sujeito
a erro humano — dois arquivos diferentes com o mesmo "v1"), a versão é
derivada do hash SHA-256 do conteúdo do arquivo. O mesmo conteúdo sempre gera
o mesmo `PromptVersion` (idempotente); qualquer mudança de um caractere gera
uma versão nova automaticamente. `name` é fornecido pelo usuário (rótulo
legível, ex. "service-desk-system-prompt"); `version` é o hash abreviado
(primeiros 12 caracteres do hash, prática comum em VCS).

## Escopo

### Dentro do escopo (V1.5)

- Tabela `prompt_version` (schema SQL).
- `engine/prompts/models.py` — `PromptVersion`.
- `engine/prompts/repository.py` — `get_or_create_prompt_version(content) ->
  PromptVersion` (hash-based, idempotente).
- CLI: `evaluate --prompt-file`.
- `experiment.prompt_version_id` (coluna nova).

### Fora do escopo (fases futuras)

- UI dedicada para "prompt diffing" (mostrar o que mudou entre duas versões
  lado a lado) — não pedido ainda; a comparação de accuracy via `/compare`
  já existente cobre o caso de uso essencial.
- Templates de prompt com variáveis — fora de escopo enquanto não há
  provider real consumindo isso.

## Critérios de aceitação

- [ ] Dois arquivos de prompt com conteúdo idêntico (mesmo hash) resultam no
      mesmo `PromptVersion` — idempotência confirmada mesmo com nomes de
      arquivo diferentes.
- [ ] Um arquivo de prompt alterado (1 caractere) gera um `PromptVersion`
      novo, com hash diferente.
- [ ] `evaluate --prompt-file` sem essa flag continua funcionando
      exatamente como antes (retrocompatibilidade — `prompt_version_id`
      fica `None`).
- [ ] `experiment.prompt_version_id` é persistido corretamente quando a
      flag é usada.
