# O que Traria Avanco Significativo para o IntelliCare e Plano Resumido

## Resumo executivo

O maior ganho que o IntelliCare pode extrair dessa abordagem nao e "criar squads", e sim implantar um pequeno sistema de engenharia assistida por IA com quatro pilares:

1. contexto estruturado por demanda e por modulo;
2. memoria operacional persistente;
3. gates deterministicos + gates semanticos;
4. classificacao explicita do tipo de execucao: Worker, Agent, Hybrid ou Human.

Se isso for implementado de forma enxuta, o ganho para a plataforma pode ser grande em qualidade, velocidade e reducao de retrabalho.

## O que eu traria para o IntelliCare com maior impacto

### 1. Memory Layer pragmatica para o repositorio

Trazer para o IntelliCare:

- `patterns` por modulo
- `gotchas` por demanda/modulo
- `session digests` curtos por entrega relevante

Aplicacao no IntelliCare:

- `modules/*` e `frontend/*` passam a ter historico operacional reutilizavel
- problemas recorrentes de staging, auth, build, docker, rotas, multitenancy e careplanner deixam de depender de memoria humana
- novos agentes/devs passam a errar menos em temas repetitivos

Exemplos concretos:

- gotchas de `tenant_session`, `schema tenant_{slug}`, `router prefix`, `static assets`, `build regenerando packages/intellicare-core/static`, `webhook HMAC`, `TaskStatus`
- patterns de `repository -> service -> router`, `tests integration`, `frontend hooks + pages`, `docker compose staging`

### 2. Brownfield documentation focada por impacto

Trazer para o IntelliCare:

- antes de mexer em modulo existente, gerar um mini-mapa da area afetada
- documentar somente o que a demanda toca, nao o sistema inteiro

Aplicacao:

- para cada DEM relevante, produzir um artefato tipo:
  - contexto atual
  - arquivos afetados
  - contratos/API impactados
  - riscos de regressao
  - dados/migrations envolvidos
  - smoke tests de confirmacao

Isso combina muito com a realidade do IntelliCare, que e brownfield modular e com frequentes mudancas cruzando backend, frontend e infra.

### 3. Gates operacionais mais formais no workflow de demanda

Trazer para o IntelliCare:

- quality gates pequenos e objetivos no fim de cada demanda
- distinguir falhas blocking de warnings

Aplicacao:

- gate estrutural:
  - docs minimas existem
  - rotas/contratos atualizados
  - migration presente quando schema muda
- gate tecnico:
  - build/test/lint/pytest relevantes passam
- gate de integracao:
  - endpoints principais e fluxos UI sao validados
- gate operacional:
  - staging/deploy checklist quando a demanda exigir

Isso fortaleceria o nosso fluxo `01_FUNCIONAL -> 02_TECNICA -> 03_PLANO -> 04_DIARIO -> 05_FINALIZACAO`.

### 4. Classificacao explicita Worker vs Agent vs Hybrid vs Human

Esse e um conceito muito valioso para o IntelliCare.

Aplicacao direta:

- Worker:
  - migracoes, seeds, jobs deterministicos, calculos, integrações bem definidas
- Agent:
  - sumarizacao, triagem textual, sugestoes, classificacao heuristica
- Hybrid:
  - condutas clinicas assistidas, encounter drafts, follow-up planner, revisao de resposta do paciente
- Human:
  - decisoes clinicas, aprovacoes criticas, configuracao sensivel, operacoes LGPD

Esse enquadramento melhora desenho de sistema, seguranca e governanca. Para saude, isso e particularmente importante.

### 5. Captura de padroes de implementacao reutilizaveis

Trazer para o IntelliCare:

- bibliotecas internas de padroes de modulo, testes, hooks, pagina list/detail/form, workers, webhooks, SSE, metrics e deploy

Aplicacao:

- um catalogo em `docs/design-docs/` ou `docs/patterns/`
- exemplo:
  - padrao de modulo FastAPI carregado dinamicamente
  - padrao de migration
  - padrao de teste de integracao async
  - padrao de page Gestor/Admin/Paciente
  - padrao de webhook seguro
  - padrao de worker Redis

Isso diminui divergencia entre DEMs e melhora consistencia arquitetural.

## O que NAO vale trazer agora

- sistema complexo de mind cloning
- formalizacao pesada de tiers de experts
- autoridade de git/push baseada em "persona"
- proliferacao de agentes para tudo

Esses itens trazem pouco retorno para o estado atual do IntelliCare e aumentam custo operacional.

## Plano resumido de implementacao para o IntelliCare

### Fase 1. Fundacao leve de conhecimento operacional

Objetivo:
criar memoria util sem mudar o processo central.

Entregas:

- `docs/patterns/README.md`
- `docs/patterns/backend-modules.md`
- `docs/patterns/frontend-pages.md`
- `docs/patterns/workers-webhooks.md`
- `docs/gotchas/README.md`
- `docs/gotchas/careplanner.md`
- `docs/gotchas/staging-deploy.md`
- `docs/gotchas/keycloak-auth.md`

Regra operacional:

- toda DEM que gerar aprendizado recorrente adiciona ou atualiza `pattern` ou `gotcha`

### Fase 2. Template de brownfield por demanda

Objetivo:
padronizar leitura de contexto antes da execucao.

Entregas:

- novo template opcional em `docs/demandas/*/00_CONTEXTO_BROWNFIELD.md`
- checklist curto no `03_PLANO.md`:
  - area impactada
  - contratos afetados
  - migration?
  - riscos de regressao
  - estrategia de validacao

Uso inicial:

- obrigatorio apenas para DEMs que alterem 2+ camadas ou staging/infra

### Fase 3. Gates de validacao por tipo de demanda

Objetivo:
deixar "pronto" mais objetivo e menos interpretativo.

Entregas:

- matriz de gates por categoria:
  - backend
  - frontend
  - infra
  - e2e
  - integracao
- checklist de blocking vs warning

Exemplo:

- blocking:
  - build quebrado
  - migration faltando
  - rota sem teste basico em modulo critico
- warning:
  - cobertura parcial de E2E
  - docs auxiliares ausentes

### Fase 4. Matriz de execucao Worker/Agent/Hybrid/Human

Objetivo:
governar melhor automacoes do IntelliCare, especialmente no CarePlanner e nos fluxos clinicos.

Entregas:

- `docs/design-docs/execution-matrix.md`
- classificacao inicial dos modulos:
  - admin
  - gestor
  - cuidado
  - florence
  - oswaldo
  - careplanner

Aplicacao imediata:

- revisar jobs e automacoes que hoje misturam decisao heuristica com acao deterministica
- separar claramente onde precisa aprovacao humana

### Fase 5. Ferramenta simples de captura de digest

Objetivo:
reter contexto util entre sessoes e entregas.

Entregas:

- script simples para gerar digest de sessao/DEM
- armazenamento em `docs/digests/`
- campos minimos:
  - demanda
  - decisao tomada
  - arquivos criticos
  - riscos
  - gotchas
  - validacao executada

## Ordem recomendada

Se for para fazer com maximo retorno e minimo custo:

1. Fase 1
2. Fase 2
3. Fase 3
4. Fase 4
5. Fase 5

## Resultado esperado

Se essas cinco fases forem implantadas de forma enxuta, o IntelliCare deve ganhar:

- menos retrabalho entre DEMs
- menos regressao por perda de contexto
- onboarding tecnico mais rapido
- melhor seguranca em automacoes
- especificacoes mais executaveis
- maior consistencia entre backend, frontend, testes e staging

## Conclusao

O AIOX sugere uma direcao correta: transformar conhecimento operacional em sistema. Para o IntelliCare, o salto relevante nao e virar um ecossistema de "squads", e sim institucionalizar:

- memoria util,
- contexto de brownfield,
- gates objetivos,
- e separacao clara entre automacao deterministica e decisao assistida.

Se isso entrar no nosso fluxo de demandas, o ganho para a plataforma sera significativo e cumulativo.
