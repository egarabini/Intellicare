"""
Slides da V3 Investidores - Apresentacao para Investidores e Decisores.

Estrutura (10 slides):
  Bloco 1 - Oportunidade e Problema (2 slides)
  Bloco 2 - Solucao e Diferencial (3 slides)
  Bloco 3 - Tecnologia e Arquitetura (2 slides)
  Bloco 4 - Mercado e Fechamento (3 slides)

Foco em ROI, escalabilidade e impacto - linguagem executiva.
"""

from pathlib import Path
from typing import Dict, List

from slides.content_slide import ContentSlide
from slides.diagram_slide import DiagramSlide
from slides.metrics_slide import MetricsSlide
from slides.title_slide import TitleSlide
from slides.agent_profile_slide import AgentProfileSlide
from slides.integration_flow_slide import IntegrationFlowSlide


def _resolve_agent_image(agent_key: str) -> str:
    """Resolve caminho da imagem do agente (estilo real/IA)."""
    images_dir = Path(__file__).resolve().parents[2] / "assets" / "images"
    style_map = {
        "wanda": "agente_wanda_ia.png",
        "florence": "agente_florence_ia.png",
        "oswaldo": "agente_oswaldo_ia.png",
        "zilda": "agente_zilda_arns_ia.png",
        "geralda": "agente_geralda_ia.png",
        "nise": "agente_nise_ia.png",
        "donabedian": "agente_donabedian_ia.png",
        "minerva": "agente_minerva_ia.png",
        "pierre": "agente_pierre_ia.png",
    }
    filename = style_map.get(agent_key)
    if not filename:
        return ""
    return str(images_dir / filename)


def create_v3_investidores_slides(image_style: str = "real") -> List:
    """Cria os 10 slides da versao V3 Investidores."""
    slides: List = []

    # ================================================================
    # BLOCO 1 - OPORTUNIDADE E PROBLEMA (2 slides)
    # ================================================================

    # -- Slide 1: Titulo --
    slide1 = TitleSlide(
        title="IntelliCare",
        subtitle="Inteligencia Artificial Coordenada para Saude",
        narration=(
            "Bem-vindos. Eu sou a Wanda, a inteligencia que orquestra "
            "o IntelliCare. Nos proximos minutos, vou mostrar como "
            "transformamos dados clinicos fragmentados em decisoes "
            "coordenadas e seguras. Um ecossistema de agentes "
            "inteligentes, cada um inspirado em um gigante da saude. "
            "Vamos comecar pelo problema."
        ),
    )
    slide1.narration_rate = 155
    slides.append(slide1)

    # -- Slide 2: O Problema --
    slide2 = ContentSlide(
        title="O Problema: Fragmentacao Clinica",
        content=[
            "70% dos erros clinicos envolvem falha de comunicacao entre equipes",
            "Dados de laboratorio, cronicos e territorio em silos separados",
            "Profissionais sem visao integrada do paciente no ponto de cuidado",
            "Sistemas legados sem interoperabilidade: HL7v2, XML, planilhas",
        ],
        narration=(
            "O problema e claro: a saude brasileira sofre com fragmentacao. "
            "Dados de exames ficam em um sistema, historico de cronicos em outro, "
            "e a rede assistencial em um terceiro. O profissional de saude nao "
            "tem uma visao integrada. Setenta por cento dos erros clinicos "
            "envolvem falha de comunicacao. IntelliCare resolve isso."
        ),
    )
    slide2.narration_rate = 155
    slide2.deep_dive_content = {
        "title": "Dados de Mercado - Fragmentacao",
        "content": (
            "- WHO: erros medicos sao a 3a causa de morte nos EUA\n"
            "- ANS: 48 milhoes de beneficiarios, dados fragmentados\n"
            "- SUS: 150 milhoes de usuarios, interoperabilidade minima\n"
            "- Custo estimado de erros evitaveis: R$ 22 bi/ano (IESS 2024)"
        ),
    }
    slides.append(slide2)

    # ================================================================
    # BLOCO 2 - SOLUCAO E DIFERENCIAL (3 slides)
    # ================================================================

    # -- Slide 3: A Solucao --
    slide3 = ContentSlide(
        title="A Solucao: Agentes Coordenados",
        content=[
            "7 agentes especializados, cada um com dominio clinico definido",
            "Orquestracao inteligente: a pergunta certa para o agente certo",
            "Interoperabilidade nativa FHIR R4 e IPS Brasil",
            "Seguranca: IPS-First, anti-fabricacao, rastreabilidade completa",
        ],
        narration=(
            "O IntelliCare e um ecossistema de sete agentes inteligentes, "
            "cada um especialista em um dominio: clinica profunda, cronicos, "
            "territorio, acompanhamento, qualidade, educacao. Eu, Wanda, "
            "sou a orquestradora: recebo a pergunta, identifico quais agentes "
            "acionar, agrego as respostas e aplico regras de seguranca. "
            "Tudo nativo em FHIR R4, o padrao internacional de saude."
        ),
    )
    slide3.narration_rate = 155
    slide3.deep_dive_content = {
        "title": "Arquitetura LEGO",
        "content": (
            "- Cada modulo funciona de forma independente\n"
            "- APIs REST padronizadas: /api/v1/health, /api/v1/info\n"
            "- Comercializacao individual ou ecossistema completo\n"
            "- Deploy containerizado (Docker Compose)\n"
            "- Schemas separados: operacional e analitico"
        ),
    }
    slides.append(slide3)

    # -- Slide 4: Os Agentes (resumo executivo) --
    slide4 = MetricsSlide(
        title="Os 7 Agentes Especializados",
        subtitle="Cada nome homenageia um gigante da saude",
        metrics=[
            {
                "label": "WANDA",
                "value": "Orquestradora",
                "icon": "W",
                "description": "Wanda de Aguiar Horta - coordena tudo",
            },
            {
                "label": "FLORENCE",
                "value": "Clinica",
                "icon": "F",
                "description": "Nightingale - exames e evidencias",
            },
            {
                "label": "OSWALDO",
                "value": "Cronicos",
                "icon": "O",
                "description": "Cruz - diabetes, renal, HAS",
            },
            {
                "label": "DONABEDIAN",
                "value": "Qualidade",
                "icon": "D",
                "description": "Pai da qualidade em saude",
            },
        ],
        narration=(
            "Nossos sete agentes: Wanda orquestra. Florence analisa exames "
            "com rigor cientifico. Oswaldo monitora doencas cronicas. "
            "Zilda traz dados de saude publica brasileira. Geralda acompanha "
            "o paciente no dia a dia. Nise educa profissionais. E Donabedian "
            "garante qualidade e melhoria continua. Cada nome carrega um "
            "legado, cada agente entrega valor."
        ),
    )
    slide4.narration_rate = 155
    slide4.deep_dive_content = {
        "title": "7 Agentes - Detalhamento",
        "content": (
            "WANDA: Orquestradora (porta 8007) - 93% cobertura, 69 testes\n"
            "FLORENCE: Clinica profunda (porta 8002) - 27 exames, RAG\n"
            "OSWALDO: Cronicos (porta 8001) - 85% cobertura, 127 testes\n"
            "ZILDA: Saude publica (porta 8003) - CNES, territorio\n"
            "GERALDA: Acompanhamento (porta 8006) - 96% cobertura, 108 testes\n"
            "NISE: Educacao (porta 8000) - Chatbot, RAG, Flowise\n"
            "DONABEDIAN: Qualidade (porta 8004) - 80% cobertura, 277 testes"
        ),
    }
    slides.append(slide4)

    # -- Slide 5: Caso de Uso Pratico --
    slide5 = IntegrationFlowSlide(
        title="Caso de Uso: Diabetes Descompensada",
        case_title="Consulta clinica integrada",
        steps=[
            {"agents": "PORTAL",                 "label": "1.", "detail": "Medico faz pergunta"},
            {"agents": "WANDA",                   "label": "2.", "detail": "Analisa e roteia a query"},
            {"agents": "FLORENCE, OSWALDO",        "label": "3.", "detail": "Exames + estadiamento DM2"},
            {"agents": "ZILDA",                    "label": "4.", "detail": "Rede assistencial local"},
            {"agents": "GERALDA",                  "label": "5.", "detail": "Plano de acompanhamento"},
            {"agents": "DONABEDIAN",               "label": "6.", "detail": "Registro de qualidade"},
            {"agents": "WANDA",                    "label": "7.", "detail": "Resposta consolidada"},
        ],
        narration=(
            "Veja na pratica. Um medico atende paciente com diabetes descompensada. "
            "Ele pergunta pelo portal. Eu, Wanda, entendo que preciso acionar "
            "Florence para analisar exames recentes, Oswaldo para avaliar o "
            "estadiamento da diabetes, Zilda para verificar a rede de saude "
            "local. Com as respostas, Geralda monta o plano domiciliar e "
            "Donabedian registra os indicadores. Tudo integrado, rastreavel, seguro. "
            "Sete agentes, uma resposta completa em segundos."
        ),
    )
    slide5.narration_rate = 152
    slide5.deep_dive_content = {
        "title": "Fluxo Tecnico Completo",
        "content": (
            "1. Query entra via REST (Portal ou Rocket.Chat)\n"
            "2. Wanda classifica intencao (keyword ou LLM)\n"
            "3. IPS-First: carrega sumario do paciente\n"
            "4. Routing paralelo para 2-3 agentes\n"
            "5. Agregacao inteligente (LLM ou template)\n"
            "6. Safety post-check (contradicoes, alertas)\n"
            "7. Resposta JSON estruturada ao frontend"
        ),
    }
    slides.append(slide5)

    # ================================================================
    # BLOCO 3 - TECNOLOGIA E ARQUITETURA (2 slides)
    # ================================================================

    # -- Slide 6: Stack Tecnologico --
    slide6 = MetricsSlide(
        title="Stack Tecnologico",
        subtitle="Infraestrutura cloud-ready e open-source",
        metrics=[
            {
                "label": "Backend",
                "value": "FastAPI",
                "icon": "B",
                "description": "Python, async, alto throughput",
            },
            {
                "label": "Interop",
                "value": "FHIR R4",
                "icon": "I",
                "description": "HL7 + IPS Brasil nativo",
            },
            {
                "label": "IA / LLM",
                "value": "Ollama",
                "icon": "A",
                "description": "LLM local, sem vendor lock-in",
            },
            {
                "label": "Auth",
                "value": "Keycloak",
                "icon": "K",
                "description": "SSO, RBAC, LGPD-ready",
            },
        ],
        narration=(
            "Sobre tecnologia: todo o backend e FastAPI assincrono, "
            "com PostgreSQL, Redis e RabbitMQ. Interoperabilidade nativa "
            "FHIR R4, compativel com a RNDS. IA via Ollama, sem "
            "dependencia de cloud proprietaria. Autenticacao com Keycloak "
            "integrado a SSO institucional. Tudo containerizado com Docker, "
            "pronto para escalar."
        ),
    )
    slide6.narration_rate = 155
    slide6.deep_dive_content = {
        "title": "Stack Completo",
        "content": (
            "Backend: FastAPI (Python 3.12+), Pydantic V2\n"
            "Banco: PostgreSQL 15+ (schemas separados)\n"
            "Cache/Streams: Redis 7+\n"
            "Mensageria: RabbitMQ (AMQP)\n"
            "Auth: Keycloak + SSO + RBAC\n"
            "IA: Ollama (Llama 3.1, local), Flowise (RAG)\n"
            "OCR: Surya + Llama 4 Vision (MCP Server)\n"
            "Comunicacao: Jitsi + Rocket.Chat\n"
            "Deploy: Docker Compose, CI/CD ready\n"
            "Monitoramento: Prometheus + Grafana"
        ),
    }
    slides.append(slide6)

    # -- Slide 7: Arquitetura --
    slide7 = DiagramSlide(
        title="Arquitetura do Ecossistema",
        diagram=(
            "                    PORTAL (Dashboard)\n"
            "                         |\n"
            "                      WANDA\n"
            "                   Orquestradora\n"
            "                    /    |    \\\n"
            "              FLORENCE  OSWALDO  ZILDA\n"
            "              Clinica   Cronicos  Territorio\n"
            "                    \\    |    /\n"
            "               GERALDA  NISE  DONABEDIAN\n"
            "               Seguim.  Educ.  Qualidade\n"
            "                         |\n"
            "              MCP: MINERVA + PIERRE\n"
            "               OCR       Supervisao"
        ),
        narration=(
            "A arquitetura segue o padrao LEGO: cada modulo funciona "
            "independente, mas integrado ao ecossistema. O portal e a "
            "interface. Wanda orquestra no centro. Os agentes processam "
            "em paralelo. E na base, os servidores MCP: Minerva para "
            "OCR de documentos clinicos e Pierre para supervisao de "
            "indicadores. Modular, escalavel, comercializavel."
        ),
    )
    slide7.narration_rate = 155
    slide7.deep_dive_content = {
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
    slides.append(slide7)

    # ================================================================
    # BLOCO 4 - MERCADO E FECHAMENTO (3 slides)
    # ================================================================

    # -- Slide 8: Mercado e Oportunidade --
    slide8 = ContentSlide(
        title="Mercado e Oportunidade",
        content=[
            "Saude digital no Brasil: R$ 47 bi em 2025 (ANAHP)",
            "RNDS e FHIR obrigatorios: regulamentacao a favor",
            "48M beneficiarios ANS + 150M SUS = mercado massivo",
            "Modelo SaaS: licenciamento por modulo ou ecossistema",
        ],
        narration=(
            "O mercado esta pronto. A saude digital brasileira movimenta "
            "quarenta e sete bilhoes de reais. A RNDS e o FHIR estao se "
            "tornando obrigatorios. Sao quarenta e oito milhoes de "
            "beneficiarios na ANS e cento e cinquenta milhoes no SUS. "
            "Nosso modelo permite licenciar por modulo individual ou "
            "ecossistema completo. Escalabilidade desde clinicas ate "
            "redes hospitalares."
        ),
    )
    slide8.narration_rate = 155
    slide8.deep_dive_content = {
        "title": "Modelo de Negocio",
        "content": (
            "Tier 1 - Clinica Individual:\n"
            "  FLORENCE + OSWALDO (R$ X/mes)\n\n"
            "Tier 2 - Rede de Saude:\n"
            "  Ecossistema completo (R$ Y/mes)\n\n"
            "Tier 3 - Gestao Publica:\n"
            "  DONABEDIAN + ZILDA (R$ Z/mes)\n\n"
            "Diferenciais competitivos:\n"
            "- Unico com 7 agentes coordenados\n"
            "- FHIR R4 nativo (nao adapter)\n"
            "- LLM local (sem custo de API)\n"
            "- Stack 100% open-source"
        ),
    }
    slides.append(slide8)

    # -- Slide 9: Metricas de Maturidade --
    slide9 = MetricsSlide(
        title="Maturidade do Produto",
        subtitle="Numeros reais de desenvolvimento",
        metrics=[
            {
                "label": "Testes",
                "value": "700+",
                "icon": "T",
                "description": "Automatizados, cobertura >80%",
            },
            {
                "label": "Agentes",
                "value": "7",
                "icon": "A",
                "description": "Producao-ready com APIs REST",
            },
            {
                "label": "Ferramentas MCP",
                "value": "12",
                "icon": "M",
                "description": "OCR, busca, analise, supervisao",
            },
            {
                "label": "Interoperabilidade",
                "value": "FHIR",
                "icon": "F",
                "description": "R4 nativo, IPS Brasil",
            },
        ],
        narration=(
            "Nao e promessa, e produto. Mais de setecentos testes "
            "automatizados. Sete agentes com APIs em producao. "
            "Doze ferramentas MCP para OCR, busca e analise. "
            "Interoperabilidade FHIR R4 nativa. O IntelliCare nao "
            "e um conceito, e uma plataforma funcional."
        ),
    )
    slide9.narration_rate = 155
    slide9.deep_dive_content = {
        "title": "Numeros Detalhados",
        "content": (
            "Testes por modulo:\n"
            "- WANDA: 69 testes, 93% cobertura\n"
            "- OSWALDO: 127 testes, 85% cobertura\n"
            "- GERALDA: 108 testes, 96% cobertura\n"
            "- DONABEDIAN: 277 testes, 80% cobertura\n"
            "- ZILDA: 68 testes, 95% cobertura\n"
            "- MINERVA (OCR): 37 testes\n"
            "- PIERRE (SuperZ): 29 testes\n\n"
            "Total: ~715 testes automatizados"
        ),
    }
    slides.append(slide9)

    # -- Slide 10: Fechamento --
    slide_final = TitleSlide(
        title="IntelliCare",
        subtitle="Inteligencia coordenada. Cuidado integrado. Saude real.",
        narration=(
            "IntelliCare: sete agentes inspirados em gigantes da saude. "
            "Uma orquestradora que integra, protege e entrega valor. "
            "Interoperabilidade nativa, LLM local, arquitetura modular. "
            "Estamos prontos para transformar o cuidado em saude no Brasil. "
            "Obrigada pela atencao. Vamos conversar?"
        ),
    )
    slide_final.narration_rate = 150
    slide_final.deep_dive_content = {
        "title": "Proximos Passos",
        "content": (
            "1. Piloto em rede de atencao primaria\n"
            "2. Certificacao SBIS / validacao ANS\n"
            "3. Integracao RNDS homologada\n"
            "4. Rodada de investimento Seed\n\n"
            "Contato: equipe@intellicare.com.br\n"
            "Repositorio: github.com/intellicare"
        ),
    }
    slides.append(slide_final)

    return slides
