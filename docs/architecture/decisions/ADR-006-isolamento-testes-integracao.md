# ADR-006: Testes de integração não podem mais usar TRUNCATE cego no Neon compartilhado

## Status
Aceito

## Contexto
Os testes de integração (`tests/integration/test_repository.py`,
`test_experiments.py`, `test_regression.py`) usavam fixtures com
`TRUNCATE trace_event, trace, evaluation_result, experiment, agent_version,
agent, dataset RESTART IDENTITY CASCADE` no setup, pensando nisso como
"limpar o ambiente de teste". Só que o mesmo banco Neon é usado tanto para
os testes quanto para os dados reais de demonstração criados via
`agentlab evaluate --agent` (os experimentos que alimentam o Dashboard).

Ao rodar a suíte de integração completa depois de já ter criado experimentos
reais de demonstração, o `TRUNCATE ... CASCADE` apagou esses dados —
descoberto quando `agentlab regression run` retornou `0.0%` de accuracy para
dois experimentos que sabíamos ter 91.7%.

## Decisão
1. **Curto prazo (aplicado agora)**: cada teste de integração passa a
   limpar apenas as linhas que ele mesmo criou (via `DELETE ... WHERE id =
   ...` no teardown), nunca `TRUNCATE` de tabela inteira. Onde `TRUNCATE`
   ainda for necessário (ex. teste de idempotência de schema), fica restrito
   a tabelas que não guardam dados de demonstração (nenhuma, atualmente —
   se precisar, requer um ADR próprio).
2. **Médio prazo (registrado como débito técnico, não implementado agora)**:
   usar uma branch separada do Neon (recurso nativo do Neon — cria uma cópia
   isolada do banco) só para CI/testes de integração, nunca compartilhando
   dados com o ambiente de desenvolvimento/demonstração. Isso remove de vez
   a possibilidade de um teste afetar dado real, independente de qualquer
   disciplina de limpeza cirúrgica.

## Consequências
- Dados de demonstração recriados manualmente após o incidente (reprodutível
  em segundos via `agentlab evaluate`, sem perda real — eram dados
  sintéticos de MVP, não produção).
- Testes de integração ficam levemente mais verbosos (limpeza explícita por
  id em vez de um `TRUNCATE` genérico), mas seguros para rodar a qualquer
  momento sem risco de destruir dado real.
- A spec de CI/CD (próxima) deve decidir se usa uma branch Neon dedicada ou
  um Postgres efêmero do próprio GitHub Actions — qualquer uma resolve o
  problema de raiz; a escolha fica para aquela spec.
