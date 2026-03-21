# ADR-002 — Módulo Marie: Orquestrador de IA Avançada (Dify como Microsserviço Parceiro)

**Status:** `PROPOSTO` — aguarda gatilho de implementação
**Data:** 2026-03-21
**Autor:** Eduardo (ARQUITETO)
**Referência:** ADR-001 (Executor Matrix) — Marie é classificada como `Agent` na camada de Processamento IA

---

## Contexto

A IntelliCare V3 hoje possui dois módulos clínicos com integração LLM:

- **Florence** (`modules/florence/`) — sugestão de notas SOAP via `POST /florence/notes/suggest`
- **Oswaldo** (`modules/oswaldo/`) — sugestão de prescrição + CID-10 via `POST /oswaldo/suggest`

Ambos usam `shared/llm.py` — um wrapper direto sobre a API OpenAI-compatible com fallback rule-based. Os **prompts estão hardcoded em Python** (`services.py`). Qualquer alteração de prompt exige:

1. Edição de código Python por um desenvolvedor
2. Commit + CI/CD
3. Rebuild do container e redeploy no staging/produção

Esse ciclo é inviável quando a equipe clínica quiser iterar prompts com frequência — por exemplo, adaptar o raciocínio diagnóstico para especialidades diferentes, ou testar sumarizações de histórico FHIR.

**Problema adicional:** fluxos RAG mais densos (ex: cruzar histórico longitudinal do paciente + guidelines online + base local Ollama) gerariam centenas de linhas de código Python com LangChain/LlamaIndex de difícil manutenção e auditoria.

---

## Decisão

Nomear **Módulo Marie** como a identidade arquitetural do futuro orquestrador de IA avançada do IntelliCare V3, inspirado em Marie Curie: assim como ela criou os instrumentos para medir e processar elementos invisíveis, Marie será o instrumento que processa inteligência clínica complexa antes de entregá-la ao Oswaldo ou à Florence.

A abordagem escolhida é **Dify como Microsserviço Parceiro** — containers Dify rodando lado a lado com o IntelliCare no `docker-compose.yml`, acessados via API interna. O código do IntelliCare **não é alterado estruturalmente**: apenas a chamada em `shared/llm.py` ganha um segundo destino opcional.

---

## Alternativas descartadas

### ❌ Extrair engine RAG do Dify para o FastAPI
O Dify é um monólito acoplado (Next.js front + Python/Flask + Celery queues). Isolar apenas a "engine RAG" para rodar no FastAPI geraria mais trabalho estrutural do que codificar o próprio orquestrador com LangChain. **Rejeitado.**

### ❌ Substituir shared/llm.py por LangChain diretamente
Viável tecnicamente, mas deixa os prompts ainda hardcoded no código Python e não resolve a necessidade de iteração visual por clínicos não-desenvolvedores. **Rejeitado para fluxos complexos.**

### ✅ Dify como Microsserviço Parceiro (escolhida)
Sem alterar uma linha do código Dify, sem acoplamento estrutural. O IntelliCare envia `POST http://marie:5001/v1/chat-messages` e recebe JSON. Todo o RAG, vector DB, versionamento de prompts e observabilidade ficam no domínio Marie/Dify.

---

## Arquitetura proposta

```
ClinicoUI (React)
    │
    ▼
[ Oswaldo / Florence ]  ←── FastAPI modules (código IntelliCare)
    │
    │  POST /v1/chat-messages
    │  { patient_uuid, context, flow_id }
    ▼
[ Módulo Marie ]  ←── Dify containers (docker-compose)
    │
    ├── Vector DB (Weaviate ou pgvector)
    ├── RAG Engine (histórico FHIR, laudos, interações)
    ├── LLM Router (Ollama local / OpenAI fallback)
    └── Prompt Versioning (editável via UI Dify sem deploy)
    │
    ▼
JSON validado → Oswaldo (prescrição) / Florence (nota SOAP)
```

### Fluxo de chamada (exemplo Oswaldo)

```python
# modules/oswaldo/services.py — versão futura com Marie

async def suggest_prescription(ctx, encounter_id: str, complaint: str):
    if settings.MARIE_ENABLED:
        # Delega para Marie (Dify)
        return await marie_client.chat(
            flow_id=settings.MARIE_FLOW_PRESCRIPTION,
            inputs={"patient_uuid": ctx.tenant, "complaint": complaint}
        )
    else:
        # Fallback: shared/llm.py atual (rule-based + OpenAI direto)
        return await llm_suggest(complaint)
```

A flag `MARIE_ENABLED` no `.env` permite ligar/desligar Marie sem redeploy.

---

## Containers necessários (adição ao docker-compose.yml)

```yaml
# Adição futura em infra/docker-compose.yml

marie-api:
  image: langgenius/dify-api:latest
  environment:
    - SECRET_KEY=${MARIE_SECRET_KEY}
    - DB_USERNAME=marie
    - DB_PASSWORD=${MARIE_DB_PASSWORD}
    - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/2
    - VECTOR_STORE=pgvector
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - OLLAMA_BASE_URL=http://ollama:11434
  depends_on: [marie-db, redis]
  networks: [intellicare-net]

marie-worker:
  image: langgenius/dify-api:latest
  command: worker
  environment: *marie-env
  networks: [intellicare-net]

marie-web:
  image: langgenius/dify-web:latest
  environment:
    - NEXT_PUBLIC_API_PREFIX=http://marie-api:5001/console/api
  ports:
    - "8088:3000"   # UI visual para gestores clínicos editarem prompts
  networks: [intellicare-net]

marie-db:
  image: postgres:16-alpine
  environment:
    - POSTGRES_DB=marie
    - POSTGRES_USER=marie
    - POSTGRES_PASSWORD=${MARIE_DB_PASSWORD}
  volumes:
    - marie_db_data:/var/lib/postgresql/data
  networks: [intellicare-net]
```

---

## O que Marie resolve que hoje não resolvemos

| Necessidade | Hoje (shared/llm.py) | Com Marie |
|-------------|----------------------|-----------|
| Alterar prompt de prescrição | Dev commit + redeploy | Gestor clínico edita na UI Dify |
| RAG sobre histórico de 10 anos | ~500 linhas LangChain | Bloco visual no flow Dify |
| Versionar prompts | Git diff em .py | Histórico de versões nativo no Dify |
| Observar custo de tokens por clínico | Não temos | Dashboard Dify nativo |
| Testar novo modelo LLM sem código | Impossível | Trocar modelo no flow Dify |
| Cruzar FHIR externo + Ollama local | Implementação customizada | Bloco HTTP + bloco LLM no Dify |

---

## Gatilho de implementação

**NÃO implementar agora.** Marie deve ser implementada exatamente quando **qualquer uma** dessas condições for verdadeira:

1. A equipe clínica começar a solicitar alterações de prompts com frequência > 1x/semana
2. Aparecer demanda de RAG longitudinal (histórico > 6 meses, FHIR, laudos externos)
3. Surgir necessidade de comparar 2+ modelos LLM em produção simultaneamente
4. Oswaldo ou Florence precisarem de mais de 3 etapas encadeadas de LLM para gerar uma resposta

Enquanto esses gatilhos não ocorrerem, `shared/llm.py` com OpenAI-compatible + fallback rule-based é suficiente e mais simples de operar.

---

## Linhagem dos módulos clínicos

```
shared/llm.py          — camada 0: wrapper direto LLM (hoje)
    │
    ├── Florence        — notas clínicas SOAP/FREE (usa shared/llm)
    ├── Oswaldo         — prescrições + CID-10 (usa shared/llm)
    │
    └── Marie (futura) — orquestradora: Florence e Oswaldo perguntam
                         para Marie em fluxos complexos; Marie consulta
                         o histórico completo, processa via RAG/LLM e
                         devolve a resposta validada
```

**Nomenclatura:** Assim como Pierre Curie é a fundação (infra/dados) e Florence Nightingale e Oswaldo Cruz são os clínicos especializados, **Marie Curie** é quem cria os instrumentos para medir e transformar o invisível em conhecimento. Marie não substitui Florence nem Oswaldo — ela **amplifica** o que eles podem oferecer.

---

## Licença e auditoria

Dify é open source Apache 2.0. Todo o código pode ser auditado. A adoção como microsserviço não exige fork ou modificação — apenas pull da imagem oficial e configuração via variáveis de ambiente.

---

## Próximos passos (quando o gatilho for acionado)

- [ ] Criar `DEM-069 Módulo Marie — Bootstrap Dify + marie_client.py`
- [ ] Adicionar `marie-api`, `marie-worker`, `marie-web`, `marie-db` ao `docker-compose.yml`
- [ ] Implementar `packages/intellicare-core/intellicare_core/marie_client.py`
- [ ] Criar flag `MARIE_ENABLED` no settings e `.env.example`
- [ ] Migrar primeiro flow: Oswaldo prescrição → Marie RAG
- [ ] Smoke no staging: `POST /oswaldo/suggest` → Marie flow ativo
