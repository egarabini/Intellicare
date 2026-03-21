# ADR-001 - Executor Matrix: Governanca de Automacao IntelliCare

- **Status:** Accepted
- **Data:** 2026-03-28
- **Decisores:** ARQUITETO (Eduardo Garabini)
- **Contexto tecnico:** IntelliCare V3 - FastAPI + Redis workers + Kestra + 4 canais CarePlanner

## Contexto e Problema

O IntelliCare V3 ja opera com automacoes reais em varias camadas: workers Redis do
CarePlanner, adapters de canal, flows Kestra, ingestao vetorial, certificados ACME,
assistencia por IA no frontend clinico e rotinas operacionais de staging.

O problema e que esses executores cresceram sem uma classificacao formal compartilhada.
Na pratica, um dev novo consegue localizar `dispatcher_worker`, `trigger_flow()` ou
`WhatsAppAdapter.send_message()`, mas nao encontra no projeto uma resposta objetiva para
estas perguntas:

- esse componente pode rodar livremente em background?
- ele so altera estado interno ou produz efeito externo irreversivel?
- existe ponto obrigatorio de aprovacao humana?
- se der erro, basta retry tecnico ou o problema exige trilha de auditoria?

Sem essa classificacao, guardrails ficam implícitos e acabam vivendo na memoria de
sprint, nao no repositorio. Isso ja e especialmente sensivel no CarePlanner
multicanal, onde uma mesma jornada cruza Redis, Kestra, WhatsApp, email, SMS,
Rocket.Chat e notificacoes internas.

Esta decisao deriva da recomendacao da Camada 2 do IA-FRAMEWORK em
`IA-FRAMEWORK/CONCLUSAO/CONCLUSAO_ARQUITETO.md`, depois da entrega de memoria
operacional da DEM-INF (`patterns`, `gotchas`, `HANDOFF.yml`).

## Decisao

Adotar a **Executor Matrix** como criterio formal de classificacao de toda automacao do
IntelliCare, com quatro categorias:

- **Worker:** executa sozinho, com efeito interno, reversivel ou idempotente.
- **Agent:** executa sozinho, mas produz efeito externo real ou altera dado com
  consequencia operacional relevante. Requer rastreabilidade e auditoria.
- **Hybrid:** inicia automaticamente, mas depende de aprovacao humana antes de gerar o
  efeito final de negocio.
- **Human:** nao deve ser automatizado no estado atual do produto ou da operacao.

A classificacao passa a ser revisada pelo ARQUITETO a cada sprint e toda nova DEM que
introduzir automacao deve propor explicitamente sua categoria.

## Classificacao Atual dos Componentes

| Componente | Modulo | Categoria | Justificativa |
|---|---|---|---|
| `enqueue_dispatch()` | careplanner | Worker | Apenas serializa `correlation_id` e `tenant_slug` na fila Redis `careplanner:dispatch:queue`; efeito interno e repetivel. |
| `dispatcher_worker()` | careplanner | Agent | Consome a fila e pode culminar em envio real por WhatsApp, email, SMS ou Rocket.Chat. |
| `_do_dispatch()` | careplanner | Agent | Executa o roteamento final de canal e muda status da task apos side effect externo. |
| `expiry_worker()` | careplanner | Worker | Varre SLAs e procura tarefas expiradas periodicamente sem tocar sistemas de terceiros. |
| `_expire_for_tenant()` | careplanner | Worker | Marca tasks como `EXPIRED` e publica evento interno; alteracao reversivel por admin e auditavel no proprio sistema. |
| `WhatsAppAdapter.send_message()` | careplanner | Agent | Envia mensagem real via Evolution API para paciente; efeito externo irreversivel. |
| `EmailAdapter.send_message()` | careplanner | Agent | Envia email transacional real via Listmonk; efeito externo irreversivel. |
| `SMSAdapter.send_message()` | careplanner | Agent | Envia SMS real via Jasmin; ha custo operacional e irreversibilidade pratica. |
| `RocketChatAdapter.post_message()` | careplanner | Agent | Publica mensagem em sala real do Rocket.Chat; impacto operacional fora do processo local. |
| `KestraAdapter.trigger_flow()` | careplanner | Hybrid | Dispara execucao externa no Kestra que pode continuar automacoes posteriores; precisa de insumos corretos e rastreaveis para prosseguir com seguranca. |
| `KestraAdapter.resume_execution()` | careplanner | Hybrid | Retoma uma execucao pausada; na governanca desejada, deve ser usada quando um gate humano ja validou o proximo passo. |
| `notify_clinico_replied()` | careplanner | Worker | Gera notificacao interna e broadcast Redis para o tenant; nao envia para canal externo do paciente. |
| `notify_task_expired()` | careplanner | Worker | Publica alerta interno de expiracao para UI/notificacoes do tenant; sem side effect externo irreversivel. |
| `trigger_cuidado_encounter()` | careplanner | Worker | Publica evento Redis interno para o modulo de cuidado; integracao intra-plataforma, nao outbound para terceiro. |
| `generate_journey_report()` | careplanner | Worker | Monta bytes de PDF sob demanda a partir de dados existentes; sem efeito externo. |
| `render_pdf()` | intellicare-core | Worker | Funcao deterministica de renderizacao de PDF; pode falhar tecnicamente, mas nao produz efeito externo por si so. |
| `provision_flows()` (`infra/kestra/seed_flows.py`) | infra | Worker | Seed idempotente de flows via `PUT/POST` na infra Kestra do proprio ambiente; uso repetivel e controlado. |
| `scan_and_ingest()` | vector | Worker | Ingere PDF/MD/TXT da pasta observada para a knowledge base do tenant; processo interno e reexecutavel. |
| `start_watcher()` | vector | Worker | Agenda o watcher APScheduler em loop previsivel; nao cria side effect externo sozinho. |
| `SLMAssistant` / `AIAssistant` | ClinicoUI | Hybrid | Sugere resposta ou rascunho clinico ao usuario, mas o humano decide o que aproveitar e onde salvar. |
| `TenantService.create_tenant()` | admin | Human | Apesar de existir endpoint, a decisao de criar tenant continua comercial e operacional; nao deve ser liberada como automacao autonoma. |
| `deploy/staging_update.sh` | infra | Human | Requer decisao humana de timing, janela de risco, validacao de segredos e acompanhamento de rollout. |
| `Escaneio QR WhatsApp` | infra | Human | Exige presenca fisica do operador com o aparelho e nao e automatizavel hoje. |
| `Traefik ACME / certresolver letsencrypt` | infra | Worker | Emissao e renovacao de certificado ocorrem automaticamente pelo Traefik, com comportamento idempotente e interno de plataforma. |

## Consequencias

### Positivas

- Tira a discussao de automacao do campo da intuicao e coloca em artefato persistente.
- Deixa claro quais componentes exigem trilha de auditoria obrigatoria, especialmente
  `Agent`.
- Facilita onboarding: um dev novo consegue decidir com mais seguranca se um executor
  pode rodar livremente ou se precisa de guardrail.
- Reduz ambiguidades entre automacao deterministica de plataforma e assistencia clinica
  com humano no loop.

### Negativas

- Introduz um pequeno overhead documental em toda DEM que criar novo worker, adapter ou
  automacao.
- Algumas classificacoes vao precisar de revisao conforme o produto amadurecer,
  especialmente em fluxos Kestra e experiencias de IA clinica.

### Riscos

- A matriz perde valor se nao for revisada quando um componente muda de escopo.
- Um executor pode nascer como `Worker` e virar `Agent` apos ganhar side effects
  externos; se a ADR nao for atualizada, o guardrail fica desatualizado.

## Criterio de Revisao

A cada DEM que introduzir novo worker, adapter, flow automatizado, rotina operacional
ou experiencia de IA assistiva, o desenvolvedor deve propor a classificacao na propria
entrega do BRIEFING. O ARQUITETO confirma, corrige ou reclassifica no code review e,
quando necessario, atualiza este ADR.

## Exemplo de Uso Futuro

Se `FlorenceNoteEditor` for introduzido para sugerir texto clinico no modulo Florence,
a classificacao inicial proposta e **Hybrid**, porque a IA redige um rascunho, mas o
profissional decide se aproveita, edita ou descarta antes de salvar.

Se no futuro esse mesmo componente passar a auto-salvar nota clinica ou disparar
comunicacao sem revisao humana, ele deve ser reclassificado para **Agent** e ganhar
auditoria obrigatoria, trilha de aprovacao e validacao de risco clinico.
