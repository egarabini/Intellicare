"""
Slides V2.0.0 — Apresentação para Palestra

Estrutura (10 slides):
  Visão ampla do avanço IntelliCare baseada em docs/PLANNER-ANTIGRAVITY.
  Cada slide: resumo executivo + Deep Dive (tecla D) para detalhamento.

Fonte: CONTROLE_GERAL, ROADMAP_PARALELO, MULTI_TENANCY, PLANO_DEMO_INVESTIDORES
"""

from typing import List

from slides.content_slide import ContentSlide
from slides.diagram_slide import DiagramSlide
from slides.metrics_slide import MetricsSlide
from slides.title_slide import TitleSlide


def create_v2_0_0_palestra_slides() -> List:
    """Cria os 10 slides da versão V2.0.0 para palestra."""
    slides: List = []

    # ================================================================
    # SLIDE 1 — TÍTULO
    # ================================================================
    slide1 = TitleSlide(
        title="IntelliCare",
        subtitle="Uma Visão Além do Tempo",
        narration=(
            "Bem-vindos. Eu sou a Wanda. Nos proximos minutos, vou mostrar "
            "uma visao ampla do avanco que estamos implementando no IntelliCare. "
            "Multi-tenancy, novos modulos, roadmap paralelo e uma demo que "
            "leva a plataforma a um patamar alem do seu tempo. "
            "Pressione D em qualquer slide para aprofundar."
        ),
    )
    slide1.narration_rate = 150
    slide1.deep_dive_content = {
        "title": "Sobre esta Apresentacao",
        "content": (
            "Esta apresentacao consolida o planejamento em docs/PLANNER-ANTIGRAVITY.\n\n"
            "Controles:\n"
            "- ESPACO/Clique: Proximo slide\n"
            "- Backspace: Slide anterior\n"
            "- D: Deep Dive (detalhamento)\n"
            "- R: Repetir narracao\n"
            "- M: Mute\n"
            "- ESC: Sair\n\n"
            "Cada slide pode ser visto de forma resumida ou com detalhamento completo."
        ),
    }
    slides.append(slide1)

    # ================================================================
    # SLIDE 2 — O QUE TEMOS HOJE
    # ================================================================
    slide2 = ContentSlide(
        title="O que temos hoje",
        content=[
            "7 agentes especializados (Wanda, Florence, Oswaldo, Zilda, Geralda, Nise, Donabedian)",
            "Modularizacao LEGO: cada modulo funciona independente",
            "Demo funcional: Portal + Pierre (IA) + Minerva (OCR)",
            "Interoperabilidade FHIR R4 nativa. IPS Brasil",
            "Stack: FastAPI, PostgreSQL, Redis, Keycloak, Docker",
        ],
        narration=(
            "Hoje o IntelliCare ja possui sete agentes especializados, cada um "
            "inspired em um gigante da saude. A arquitetura modular e tipo LEGO: "
            "cada modulo funciona independente, mas integrado. Temos demo "
            "funcional com Portal, Pierre para IA e Minerva para OCR. "
            "Tudo em FHIR R4, com stack open-source e containerizada."
        ),
    )
    slide2.narration_rate = 155
    slide2.deep_dive_content = {
        "title": "Arquitetura LEGO",
        "content": (
            "- Cada modulo = deploy independente, API REST\n"
            "- Contratos padronizados: /health, /info\n"
            "- Comercializacao individual ou ecossistema completo\n"
            "- Schemas separados: operacional e analitico\n"
            "- Zero vendor lock-in: stack 100% open-source\n"
            "- LGPD by design: pseudonimizacao, audit trail"
        ),
    }
    slides.append(slide2)

    # ================================================================
    # SLIDE 3 — MULTI-TENANCY
    # ================================================================
    slide3 = ContentSlide(
        title="Multi-Tenancy: A Evolucao",
        content=[
            "2 camadas: Plataforma (admin, billing) + Tenant (clinico)",
            "Schema por tenant: tenant_{id} no PostgreSQL",
            "Isolamento LGPD: dados clinicos nunca vazam entre tenants",
            "Token Exchange: usuario multi-org seleciona organizacao",
            "Redis com prefixo tenant:{id}: para cache isolado",
        ],
        narration=(
            "A grande evolucao e o multi-tenancy. Duas camadas: plataforma "
            "para admin e billing, tenant para dados clinicos. Cada organizacao "
            "tem seu schema isolado no PostgreSQL. Isolamento total para LGPD. "
            "Usuarios podem trocar de organizacao via Token Exchange."
        ),
    )
    slide3.narration_rate = 155
    slide3.deep_dive_content = {
        "title": "Fluxo de Onboarding",
        "content": (
            "1. SuperAdmin cadastra nova empresa no intellicare-admin\n"
            "2. Admin cria schema tenant_{id} no PostgreSQL\n"
            "3. Roda migrations no schema\n"
            "4. Cria grupo no Keycloak + usuario admin\n"
            "5. Registra em platform.tenants\n"
            "6. Inicializa intellicare-gestor para o tenant\n"
            "7. Seed data: roles padrao, configs\n"
            "8. Tenant ativo e pronto para uso"
        ),
    }
    slides.append(slide3)

    # ================================================================
    # SLIDE 4 — NOVOS MÓDULOS
    # ================================================================
    slide4 = ContentSlide(
        title="Novos Modulos",
        content=[
            "intellicare-admin: gestao SaaS, cadastro de empresas, billing, planos",
            "intellicare-gestor: gestao por tenant, usuarios, RBAC, setores",
            "F0 TenantContext: concluido. F1 a F5 em roadmap",
            "Provisionamento automatico de schemas e tenants",
            "Auditoria global (plataforma) e local (tenant)",
        ],
        narration=(
            "Dois novos modulos centrais: intellicare-admin para a plataforma "
            "SaaS, com cadastro de empresas, planos e billing. intellicare-gestor "
            "para cada organizacao gerenciar seus usuarios, permissoes e setores. "
            "O TenantContext, F0, ja esta pronto. F1 a F5 seguem no roadmap."
        ),
    )
    slide4.narration_rate = 155
    slide4.deep_dive_content = {
        "title": "Fases F0 a F5",
        "content": (
            "F0: TenantContext + Infra (DONE)\n"
            "F1: intellicare-admin (CRUD tenants, provisioning) - 2 sem\n"
            "F2: intellicare-gestor (RBAC, config tenant) - 1.5 sem\n"
            "F3: Portal multi-tenant (login, routing) - 1 sem\n"
            "F4: Modulos clinicos adaptados - 2 sem\n"
            "F5: Billing + dashboards + auditoria - 2 sem\n\n"
            "Total estimado: 45-60 dias"
        ),
    }
    slides.append(slide4)

    # ================================================================
    # SLIDE 5 — ROADMAP PARALELO
    # ================================================================
    slide5 = MetricsSlide(
        title="Roadmap Paralelo",
        subtitle="5 trilhas de implementacao",
        metrics=[
            {"label": "T1", "value": "Infra", "icon": "1", "description": "Docker, Traefik, monitoramento"},
            {"label": "T2", "value": "Multi-Tenancy", "icon": "2", "description": "F1 a F5, admin, gestor"},
            {"label": "T3", "value": "Dominios", "icon": "3", "description": "DNS, wildcard certs"},
            {"label": "T4", "value": "Hardening", "icon": "4", "description": "Auth opcional, testes"},
            {"label": "T5", "value": "Tooling", "icon": "5", "description": "Excalidraw, visualizacao"},
        ],
        narration=(
            "O roadmap e paralelo. Cinco trilhas: T1 para infraestrutura, "
            "T2 para multi-tenancy, T3 para dominios e DNS, T4 para hardening "
            "e testes, T5 para ferramentas de visualizacao. T1 e T4 podem "
            "iniciar agora. T2 depende do F0, que ja esta pronto."
        ),
    )
    slide5.narration_rate = 155
    slide5.deep_dive_content = {
        "title": "Prioridades e Dependencias",
        "content": (
            "URGENTE: T1 Seguranca + Backup, T4 Auth opcional\n"
            "ALTA: T2 Multi-Tenancy (F1+F3 em paralelo)\n"
            "NORMAL: T3 Dominios (precisa Traefik), T5 Tooling\n\n"
            "Grafo T2: F0 -> F1 -> F2 -> F5\n"
            "         F0 -> F3 -> F4\n\n"
            "F1 e F3 podem ser feitos em paralelo por DEVs diferentes."
        ),
    }
    slides.append(slide5)

    # ================================================================
    # SLIDE 6 — DEMO INVESTIDORES
    # ================================================================
    slide6 = ContentSlide(
        title="Demo Investidores",
        content=[
            "DEV 1 (Portal): Dashboard vivo, telas Chat e Upload, mocks",
            "DEV 2 (Pierre): MCP Server, web_search, analyze_text, API REST",
            "DEV 3 (Minerva): Upload PDF, parse JSON, anonymizer, visualizador",
            "Wow factor: visual + IA real + dados reais",
            "Prazo: ASAP (sprints de 1 semana)",
        ],
        narration=(
            "A demo para investidores ataca em tres frentes. DEV 1 cria o "
            "portal com dashboard vivo e telas de chat e upload. DEV 2 entrega "
            "o Pierre com busca web e analise de texto. DEV 3 a Minerva com "
            "OCR de PDFs e anonimizacao. Wow factor visual, IA real e dados reais."
        ),
    )
    slide6.narration_rate = 155
    slide6.deep_dive_content = {
        "title": "Estrategia 3 DEVs",
        "content": (
            "DEV 1 - O Showman: casca visual, integracao, mocks\n"
            "DEV 2 - O Cerebro: Tavily, Ollama, MCP Server\n"
            "DEV 3 - A Prova: Tesseract/Textract, pipeline OCR\n\n"
            "Dia 5: Integracao localhost entre os 3\n"
            "Recursos: Chave Tavily, PDFs anonimizados, prototipo\n"
            "Foco: parecer integrado e completo na hora H"
        ),
    }
    slides.append(slide6)

    # ================================================================
    # SLIDE 7 — TENANTCONTEXT (F0)
    # ================================================================
    slide7 = ContentSlide(
        title="TenantContext (F0)",
        content=[
            "JWT com claim tenant_id e tenants (array)",
            "TenantContext: tenant_id, tenant_schema, user_id, roles",
            "Schema isolado: tenant_{id}.tabela no PostgreSQL",
            "Redis: tenant:{id}:{module}:{key}",
            "Modo single-tenant: tenant_id=default funciona sem alteracao",
        ],
        narration=(
            "O TenantContext e a fundacao. O JWT traz tenant_id e a lista de "
            "tenants do usuario. O contexto propaga tenant_id, schema e roles "
            "para toda a requisicao. Cada tenant tem schema e cache Redis "
            "isolados. Em modo single-tenant, tudo funciona como antes."
        ),
    )
    slide7.narration_rate = 155
    slide7.deep_dive_content = {
        "title": "Requisitos F0",
        "content": (
            "RF-F0-001: tenant_id no JWT, 403 se ausente\n"
            "RF-F0-002: TenantContext injetavel via Depends()\n"
            "RF-F0-003: Schema tenant_{id}, nunca cross-tenant\n"
            "RF-F0-004: Redis prefixo tenant:{id}:\n"
            "RF-F0-005: Config por tenant em platform.tenant_configs\n"
            "RF-F0-006: Fluxo multi-org: selecao + Token Exchange\n\n"
            "Modulos: intellicare-core, intellicare-auth"
        ),
    }
    slides.append(slide7)

    # ================================================================
    # SLIDE 8 — STACK E ARQUITETURA
    # ================================================================
    slide8 = DiagramSlide(
        title="Stack e Arquitetura",
        diagram=(
            "         PLATAFORMA (Schema Default)\n"
            "    admin | apresentacao | portal | auth\n"
            "                    |\n"
            "              TENANT (Schema por Tenant)\n"
            "    gestor | zilda | oswaldo | florence\n"
            "    donabedian | comunicacao | geralda | wanda\n"
            "                    |\n"
            "         MCP: MINERVA (OCR) + PIERRE (SuperZ)\n"
            "                    |\n"
            "    PostgreSQL | Redis | Keycloak | FHIR R4"
        ),
        narration=(
            "A arquitetura separa plataforma e tenant. Na plataforma: admin, "
            "apresentacao, portal e auth. Nos tenants: gestor e todos os agentes "
            "clinicos. Na base, Minerva e Pierre. PostgreSQL, Redis, Keycloak "
            "e FHIR R4 completam o stack."
        ),
    )
    slide8.narration_rate = 155
    slide8.deep_dive_content = {
        "title": "Principios Arquiteturais",
        "content": (
            "- Modularidade: cada agente = deploy independente\n"
            "- Padronizacao: contratos LEGO (/health, /info)\n"
            "- Event-Driven: Redis Streams + RabbitMQ\n"
            "- Schema Separation: operacional vs analitico\n"
            "- Zero vendor lock-in: stack open-source\n"
            "- LGPD by design: pseudonimizacao, audit trail"
        ),
    }
    slides.append(slide8)

    # ================================================================
    # SLIDE 9 — MERCADO E OPORTUNIDADE
    # ================================================================
    slide9 = ContentSlide(
        title="Mercado e Oportunidade",
        content=[
            "Saude digital Brasil: R$ 47 bi em 2025 (ANAHP)",
            "RNDS e FHIR obrigatorios: regulamentacao a favor",
            "48M beneficiarios ANS + 150M SUS = mercado massivo",
            "Modelo SaaS: licenciamento por modulo ou ecossistema",
            "Unico com 7 agentes coordenados + FHIR R4 nativo",
        ],
        narration=(
            "O mercado esta pronto. Quarenta e sete bilhoes em saude digital. "
            "RNDS e FHIR obrigatorios. Quarenta e oito milhoes na ANS, cento e "
            "cinquenta no SUS. Modelo SaaS: por modulo ou ecossistema. "
            "Diferencial: unico com sete agentes coordenados e FHIR nativo."
        ),
    )
    slide9.narration_rate = 155
    slide9.deep_dive_content = {
        "title": "Modelo de Negocio",
        "content": (
            "Tier 1 - Clinica: Florence + Oswaldo\n"
            "Tier 2 - Rede: Ecossistema completo\n"
            "Tier 3 - Gestao Publica: Donabedian + Zilda\n\n"
            "Diferenciais:\n"
            "- 7 agentes coordenados (unico)\n"
            "- FHIR R4 nativo (nao adapter)\n"
            "- LLM local (sem custo de API)\n"
            "- Stack 100% open-source"
        ),
    }
    slides.append(slide9)

    # ================================================================
    # SLIDE 10 — FECHAMENTO
    # ================================================================
    slide_final = TitleSlide(
        title="IntelliCare",
        subtitle="Inteligencia coordenada. Cuidado integrado. Visao alem do tempo.",
        narration=(
            "IntelliCare: sete agentes, multi-tenancy, roadmap paralelo. "
            "Uma plataforma que evolui de modular para SaaS. "
            "Interoperabilidade nativa, LLM local, arquitetura que escala. "
            "Estamos prontos para transformar o cuidado em saude no Brasil. "
            "Obrigada pela atencao. Vamos conversar?"
        ),
    )
    slide_final.narration_rate = 150
    slide_final.deep_dive_content = {
        "title": "Proximos Passos",
        "content": (
            "1. F1 intellicare-admin + F3 Portal Multi-Tenant\n"
            "2. Demo investidores: Pierre, Minerva, Portal\n"
            "3. T1 Infra: Seguranca, Traefik, Healthchecks\n"
            "4. Piloto em rede de atencao primaria\n"
            "5. Certificacao SBIS / validacao ANS\n\n"
            "Documentacao: docs/PLANNER-ANTIGRAVITY\n"
            "Contato: equipe@intellicare.com.br"
        ),
    }
    slides.append(slide_final)

    return slides
