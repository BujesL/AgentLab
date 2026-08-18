# ADR-005: Neon (Postgres gerenciado) como banco de desenvolvimento, em vez de Docker local

## Status
Aceito

## Contexto
O plano original (ADR-002, `docs/specs/persistence/plan.md`) previa Postgres via
`docker-compose` local. Ao tentar subir o Docker Desktop na máquina de
desenvolvimento, ele falhou com "Virtualization support not detected" — a
máquina já roda dentro de um hypervisor (provavelmente uma VM corporativa
gerenciada), o que bloqueia a virtualização aninhada exigida pelo Docker
Desktop (WSL2/Hyper-V). Esse tipo de restrição normalmente só é resolvível
pelo administrador do host físico/TI, não pelo usuário local.

## Decisão
Usar **Neon** (Postgres gerenciado, camada gratuita) como banco de
desenvolvimento, apontado via `DATABASE_URL` no `.env` local (nunca
commitado). O `docker-compose.yml` continua no repositório como caminho
alternativo válido para quem tiver Docker funcional (ex. outro
desenvolvedor, CI futuro com runners que suportam containers) — não foi
removido, só não é o único caminho.

Nenhuma mudança de código foi necessária: `engine/persistence/repository.py`
já lia a conexão via `DATABASE_URL` (psycopg fala o protocolo Postgres padrão
independente de onde o banco está hospedado), reforçando que a decisão do
ADR-001/002 de não acoplar a camada de persistência a infraestrutura
específica já pagou dividendo aqui.

## Consequências
- Rodar os testes de integração (`tests/integration/test_repository.py`)
  agora depende de internet (Neon é remoto), diferente de um Postgres local.
  Os testes continuam com `pytestmark = pytest.mark.skipif` quando
  `DATABASE_URL` não está definida — não travam a suíte unitária.
- A senha da connection string do Neon foi compartilhada em texto simples
  durante esta sessão de desenvolvimento; fica registrado aqui como
  lembrete de que, ao final do trabalho neste projeto, vale rotacionar a
  senha do banco Neon por precaução (boa prática, não uma vulnerabilidade
  ativa enquanto o projeto for só de desenvolvimento/estudo).
- CI/CD futuro (Fase V1.5) precisará de uma estratégia equivalente: ou usar
  um serviço Postgres do próprio GitHub Actions (mais simples, sem
  dependência de rede externa), ou um banco de teste dedicado no Neon.
  Decisão adiada para a spec de CI/CD.
