# Agent Evaluation Lab — Visão de Produto

## Problema

Não há forma sistemática e reproduzível de responder: "esse agente de IA realmente
funciona?". Testes manuais e observação ad-hoc de respostas não capturam seleção de
ferramentas, argumentos, custo, latência ou regressões entre versões.

## Visão

Uma plataforma de engenharia (não um "LLM tester") para executar suites de avaliação
reproduzíveis contra agentes de IA, capturando o trace completo de execução (tool
calls, argumentos, resultados, tokens, custo, latência) e aplicando avaliadores
determinísticos como primeira escolha, com LLM-as-a-Judge apenas para critérios
semânticos calibrados.

## Fluxo central

```
Evaluation Case → Agent Runner → Trace → Evaluation Engine → Metrics → Experiment → Quality Gate
```

## O que este projeto NÃO é

- Não é apenas um dashboard de notas.
- Não depende de um único provedor de LLM.
- Não usa LLM como juiz de tudo — determinismo tem prioridade quando possível.
- Não expõe chain-of-thought privado nos traces.
- Não permite alteração de dados reais durante avaliações sem sandbox/mock/aprovação.
- Não acopla o Evaluation Engine diretamente ao Next.js.

## Definição de sucesso

Pegar duas versões de um agente, executá-las sobre a mesma suite, comparar métricas
via trace, identificar regressões e bloquear automaticamente (quality gate) uma
versão que não atenda aos critérios definidos — explicando onde regrediu.

## Fora de escopo no MVP

RAG evaluation, multi-agent evaluation, Groundedness, LLM-as-a-Judge, dashboard web,
prompt versioning, regression suite, quality gates automatizados em CI. Esses itens
entram nas fases V1 a V4 (ver `roadmap` em requirements.md).

## Referência

Documento-base completo: especificação recebida do usuário em 2026-08-18 (ver
histórico de conversa). Este `docs/` é a fonte de verdade operacional a partir de
agora — mudanças de escopo devem atualizar estes arquivos, não o documento original.
