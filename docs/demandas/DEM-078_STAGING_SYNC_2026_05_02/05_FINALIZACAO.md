---
tipo: finalizacao-demanda
demanda: DEM-078
titulo: Staging Sync 2026-05-02
---

# DEM-078 — Finalização de Demanda

## Resultado da Execução
O *Staging Sync 2026-05-02* foi concluído com sucesso e o ambiente de homologação está estável e operante no hash: **a4b2b94**.

As integrações dependentes dos pull requests das demandas **DEM-075**, **DEM-076** e **DEM-077** foram sincronizadas conformem solicitadas.

## Resumo das Correções Aplicadas no Sync
1. **Migrations**: 
   A inicialização e rebuild dos volumes necessitaram a inserção dos schemas SQL brutos via `psql` para suportar adequadamente o sistema de RAG/SLM e interações medicamentosas. O *018_interaction_prompts.sql* foi aplicado sem erros.

2. **Setup do Keycloak e Mock Users (Timeouts)**:
   A validação revelou que a seed de mock data (`setup_keycloak.py`) estava se esgotando no networking do Docker pela ausência de _connection pooling_ no IdP. Aplicamos a versão patcheada baseada em Sessão HTTP durável que completou a injeção do ambiente e do usário público mock `dr.silva`.

3. **Injeção do Dataset de Medicamentos (API Staging)**:
   Durante os testes o Pytest encontrou *FileNotFoundError*. A análise comprovou que o pacote estático JSON da `data/drug_interactions.json` listado na revisão de interações (DEM-077) havia sido omitido no manifesto de build (`deploy/Dockerfile`). A diretriz foi ajustada com `COPY data/ data/` e o volume estático foi pareado no rebuild.

4. **Variables Injection (POSTGRES_DB)**:
   O container API recém-nascido devolveu HTTP 500 no `check-interactions` por falha de localização da _catalog/schema_. Identificou-se que o Pydantic local caia em _fallback_ p/ 'intellicare' base devido ao omissão do repasse explicito das tags de POSTGRES no bloco API do `docker-compose.yml`. Substituímos as tags _hardcoded_ de `intellicare_dev_password` fixando a string injetora para ler as env vars `POSTGRES_USER` e `POSTGRES_DB` adequadamente.

## Validação e Qualidade
* **Integração Auth (Keycloak)**: O Token IdP de `dr.silva@demo.intellicare` (`clinico-ui`) no endpoint Token aberto do *OpenID-Connect* foi recuperado com sucesso após autorização do *directAccessGrantsEnabled*.
* **Oswaldo Check-Interactions**: Smoke cURL de AAS e Varfarina devolveu HTTP 200 reconhecendo o GRAVE a nível estático (dispensando SLM LLM calls).
* **Testes Automatizados**: A suite (`pytest`) no container Backend retornou verde (`5 passed`) na verificação primária de engine.

O ambiente de Homologação 2026-05-02 e o **Hash a4b2b94** já estão liberados para inspeção pelo QA Frontend e Product Owner.
