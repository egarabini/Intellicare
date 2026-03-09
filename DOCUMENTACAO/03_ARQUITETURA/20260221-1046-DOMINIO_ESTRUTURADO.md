# ESTRUTURANDO O DOMÍNIO

tenho dois enderecos registrados 
- intellicare.ia.br 
- saudeconectada.com.br
Vamos ver como utilizar eles na nossa plataforma e porque

Sim, você pode adotar uma estrutura híbrida de domínios para separar a plataforma principal (intellicare.ia.br como "LEGO base" SaaS/multi-tenant) dos módulos independentes (subdomínios ou saudeconectada.com.br para tenants específicos), mantendo a modularidade e escalabilidade descritas na visão LEGO e análise de multi-tenancy. [perplexity](https://www.perplexity.ai/search/097e625a-e3d4-49d2-9d83-0d31f01901b8)

## Estrutura Recomendada
Use **intellicare.ia.br** como domínio raiz para a plataforma central (admin, portal, auth), hospedando módulos de infraestrutura e orquestração. Aloque **saudeconectada.com.br** para módulos tenant-specific ou cenários isolados, facilitando vendas modulares (ex: "compre só Oswaldo via saudeconectada"). Isso evita confusão de branding e suporta cenários como UBS vs. hospital. [perplexity](https://www.perplexity.ai/search/097e625a-e3d4-49d2-9d83-0d31f01901b8)

| Domínio Principal | Uso | Exemplos de Módulos/Rotas | Vantagens |
|-------------------|-----|---------------------------|-----------|
| **intellicare.ia.br** | Plataforma SaaS/multi-tenant (camada "platform" + core) | - admin.intellicare.ia.br (gestão tenants)<br>- portal.intellicare.ia.br (login/routing)<br>- api.intellicare.ia.br/v1/{tenant_id}/oswaldo | Centraliza billing/onboarding; fácil escalar com Kubernetes/Docker; FHIR global via wildcard certs. |
| **saudeconectada.com.br** | Módulos independentes/single-tenant ou white-label | - oswaldo.saudeconectada.com.br<br>- zilda.saudeconectada.com.br/{tenant}<br>- {tenant}.saudeconectada.com.br (proxied para intellicare) | Vendas modulares ("só crônicos"); isolamento LGPD; migração fácil de monolito. |

## Configuração Técnica
- **DNS/Reverse Proxy**: Use Cloudflare/Traefik no Docker para rotear por tenant_id (do JWT Keycloak). Ex: api.intellicare.ia.br/{tenant} → schema tenant_{id} no Postgres. [perplexity](https://www.perplexity.ai/search/37413064-1917-4b87-9128-25b287741b28)
- **Certs e Subdomínios**: Wildcard SSL (*.intellicare.ia.br) para platform; certs individuais em saudeconectada para módulos autônomos.
- **Deploy**: Cada módulo em container independente (docker-compose up); Wanda orquestra via Redis Streams, filtrando por tenant. [perplexity](https://www.perplexity.ai/search/b3f59bdc-804d-471d-a6b0-be329b7c1dc9)
- **Onboarding**: Admin em intellicare provisiona schema/tenant; portal roteia para subdomínio customizado em saudeconectada se white-label.

## Impacto no Roadmap
Essa fórmula alinha com sua Fase 1-7: Comece MVP em intellicare.ia.br/core+oswaldo; expanda para multi-tenant em F0-F2 (admin/gestor). Teste com dados sintéticos RNDS/FHIR no Postgres/pgvector para simular tenants. Evite riscos LGPD com schemas isolados e audit global na platform. [perplexity](https://www.perplexity.ai/search/69437242-1bd2-49d1-9bbf-c1f6c4daf020)