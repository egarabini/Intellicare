"""
Slides da V2 - Galeria de Agentes do IntelliCare.

Foco:
- diversidade de publico
- Wanda como apresentadora
- cada agente se apresenta em primeira pessoa
"""

from pathlib import Path
from typing import Dict, List

from slides.content_slide import ContentSlide
from slides.diagram_slide import DiagramSlide
from slides.metrics_slide import MetricsSlide
from slides.title_slide import TitleSlide
from slides.agent_profile_slide import AgentProfileSlide


def _resolve_agent_image(agent_key: str, style: str) -> str:
    """Resolve caminho de imagem por agente e estilo."""
    images_dir = Path(__file__).resolve().parents[2] / "assets" / "images"

    style_map: Dict[str, Dict[str, str]] = {
        "cartoon": {
            "wanda": "wanda_cartoon.png",
            "florence": "Florence_cartoon.png",
            "oswaldo": "oswaldo_cartoon.png",
            "zilda": "zilda_cartoon.png",
            "geralda": "geralda_cartoon.png",
            "donabedian": "donabedian_cartoon.png",
            "nise": "nise_cartoon.png",
            "minerva": "minerva_cartoon.png",
            "pierre": "pierre_cartoon.png",
        },
        "real": {
            "wanda": "agente_wanda_ia.png",
            "florence": "agente_florence_ia.png",
            "oswaldo": "agente_oswaldo_ia.png",
            "zilda": "agente_zilda_arns_ia.png",
            "geralda": "agente_geralda_ia.png",
            "donabedian": "agente_donabedian_ia.png",
            "nise": "agente_nise_ia.png",
            "minerva": "agente_minerva_ia.png",
            "pierre": "agente_pierre_ia.png",
        },
        # No modo "dual", a imagem principal e a real;
        # a secundaria (cartoon) e resolvida separadamente.
        "dual": {
            "wanda": "agente_wanda_ia.png",
            "florence": "agente_florence_ia.png",
            "oswaldo": "agente_oswaldo_ia.png",
            "zilda": "agente_zilda_arns_ia.png",
            "geralda": "agente_geralda_ia.png",
            "donabedian": "agente_donabedian_ia.png",
            "nise": "agente_nise_ia.png",
            "minerva": "agente_minerva_ia.png",
            "pierre": "agente_pierre_ia.png",
        },
    }

    filename = style_map.get(style, style_map["cartoon"]).get(agent_key)
    if not filename:
        return ""
    return str(images_dir / filename)


def create_v2_slides(image_style: str = "cartoon") -> List:
    """Cria os slides da versão V2 (agentes)."""
    slides = []

    # ── Slide 1: Título ──
    slide1 = TitleSlide(
        title="IntelliCare",
        subtitle="V2 - Galeria de Agentes com a Wanda",
        narration=(
            "Olá. Eu sou a Wanda. Nesta sessão, vou apresentar nossos nove agentes "
            "e o papel de cada um no cuidado em saúde."
        ),
    )
    slide1.narration_rate = 180
    slides.append(slide1)

    # ── Slide 2: Público-alvo ──
    slide2 = ContentSlide(
        title="Para Quem Esta Apresentação Foi Desenhada",
        content=[
            "Equipes clínicas: segurança e decisão no ponto de cuidado",
            "Gestores públicos: rede assistencial e qualidade",
            "Times técnicos: arquitetura, integração e governança",
            "Cidadãos e parceiros: clareza e confiança no sistema",
        ],
        narration=(
            "Esta apresentação foi planejada para públicos diferentes, "
            "com linguagem clara para cada perfil e foco em valor prático."
        ),
    )
    slide2.narration_rate = 160
    slide2.deep_dive_content = {
        "title": "Estratégia de Comunicação por Público",
        "content": (
            "- Clínico: risco, segurança, continuidade de cuidado\n"
            "- Gestão: capacidade de rede, indicadores e priorização\n"
            "- Técnico: interoperabilidade, padrões e rastreabilidade\n"
            "- Institucional: impacto social, transparência e confiança"
        ),
    }
    slides.append(slide2)

    # ── Slide 3: Visão geral da orquestração ──
    slide3 = ContentSlide(
        title="WANDA: A Apresentadora e Orquestradora",
        content=[
            "Wanda coordena especialistas por intenção clínica e operacional",
            "Florence aprofunda análise clínica e exames",
            "Oswaldo monitora qualquer doença crônica via motor genérico",
            "Zilda organiza contexto CNES e território assistencial",
            "Geralda sustenta continuidade da jornada do paciente",
            "Donabedian conecta qualidade assistencial e gestão",
        ],
        narration=(
            "Como orquestradora, eu aciono especialistas conforme a necessidade "
            "clínica, operacional e de gestão. Assim, a resposta final é integrada."
        ),
    )
    slide3.narration_rate = 160
    slide3.deep_dive_content = {
        "title": "Fluxo de Orquestração da Wanda",
        "content": (
            "1) Entender pergunta e contexto\n"
            "2) Selecionar especialista mais adequado\n"
            "3) Consolidar respostas e riscos\n"
            "4) Entregar orientação acionável ao público certo"
        ),
    }
    slides.append(slide3)

    # ── Slides 4-9: Perfis dos agentes ──
    # narration_rate varia por agente para dar personalidade à voz
    agents = [
        {
            "key": "wanda",
            "name": "WANDA",
            "role": "Orquestradora Clínica Inteligente",
            "origin": "Wanda de Aguiar Horta",
            "represents": "Integração clínica, segurança e decisão coordenada",
            "activation": "Quando a pergunta exige raciocínio multi-domínio",
            "highlights": [
                "Coordena subagentes e ferramentas MCP",
                "Conecta clínica, gestão e território",
                "Consolida resposta única e rastreável",
            ],
            "narration": (
                "Esta sou eu, a Wanda. Minha função é integrar dados e especialistas, "
                "com foco em segurança e decisão clínica. Agora vou apresentar meus colegas."
            ),
            "rate": 180,
        },
        {
            "key": "florence",
            "name": "FLORENCE",
            "role": "Inteligência Clínica Profunda",
            "origin": "Florence Nightingale",
            "represents": "Análise clínica baseada em evidências",
            "activation": "Interpretação de exames e evolução clínica complexa",
            "highlights": [
                "Analisa tendências e sinais críticos",
                "Cruza histórico clínico e contexto atual",
                "Apoia decisão médica com objetividade",
            ],
            "narration": (
                "Esta é a Florence. Ela aprofunda a análise clínica para apoiar "
                "a tomada de decisão médica com evidências sólidas."
            ),
            "rate": 178,
        },
        {
            "key": "oswaldo",
            "name": "OSWALDO",
            "role": "Motor Genérico de Doenças Crônicas",
            "origin": "Oswaldo Cruz",
            "represents": "Monitoramento longitudinal extensível via Disease Profiles YAML",
            "activation": "Análise de progressão, estadiamento e alertas para qualquer doença crônica",
            "highlights": [
                "Motor genérico: CKD, Diabetes e Hipertensão via configuração",
                "Estadiamento plugável: KDIGO, ADA, ESC/ESH por doença",
                "Tendências, alertas e confiança em resposta estruturada",
            ],
            "narration": (
                "Este é o Oswaldo. Ele é um motor genérico de doenças crônicas. "
                "Hoje monitora doença renal, diabetes e hipertensão, "
                "e novas doenças entram apenas com um arquivo de configuração."
            ),
            "rate": 180,
            "deep_dive": {
                "title": "OSWALDO V4 - Motor Genérico de Doenças Crônicas",
                "content": (
                    "Arquitetura V4 (EF pronta):\n"
                    "- Disease Profiles em YAML: adicionar doença = novo arquivo\n"
                    "- Strategy Pattern: algoritmo de estadiamento plugável\n"
                    "- 3 perfis prontos: CKD (KDIGO), DM2 (ADA), HAS (ESC/ESH)\n\n"
                    "Exemplo de resposta estruturada:\n"
                    "- CKD: G3a/A2 — eGFR 48, queda de 8% em 90 dias\n"
                    "- HAS: Estágio 1 — PA 138/88, tendência estável\n"
                    "- Alertas com severidade + recomendações acionáveis\n"
                    "- Confidence score baseado em volume de dados"
                ),
            },
        },
        {
            "key": "zilda",
            "name": "ZILDA",
            "role": "Dados de Saúde Brasileira",
            "origin": "Zilda Arns",
            "represents": "Contexto territorial e rede assistencial brasileira",
            "activation": "Consultas CNES, tipo de unidade e região de saúde",
            "highlights": [
                "Estrutura visão de território assistencial",
                "Apoia validação e enriquecimento de CNES",
                "Conecta decisão clínica ao contexto real de rede",
            ],
            "narration": (
                "Esta é a Zilda. Ela traz contexto de rede assistencial brasileira "
                "para decisões mais realistas no território."
            ),
            "rate": 182,
        },
        {
            "key": "geralda",
            "name": "GERALDA",
            "role": "Acompanhamento do Paciente",
            "origin": "Geralda Lopes da Silva",
            "represents": "Continuidade de cuidado e vínculo com o paciente",
            "activation": "Orientação, seguimento e comunicação da jornada",
            "highlights": [
                "Traduz orientação em ações práticas",
                "Sustenta comunicação entre equipe e paciente",
                "Fortalece adesão ao plano terapêutico",
            ],
            "narration": (
                "Esta é a Geralda. Sua missão é manter o cuidado vivo "
                "entre consulta, tratamento e acompanhamento."
            ),
            "rate": 178,
        },
        {
            "key": "donabedian",
            "name": "DONABEDIAN",
            "role": "Qualidade em Saúde",
            "origin": "Avedis Donabedian",
            "represents": "Qualidade assistencial e governança por indicadores",
            "activation": "Análise de estrutura, processo, resultado e desempenho",
            "highlights": [
                "Conecta qualidade clínica e gestão",
                "Orienta melhoria contínua baseada em dados",
                "Apoia decisões com visão de eficiência e valor",
            ],
            "narration": (
                "Este é o Donabedian. Sua função é transformar dados em gestão "
                "de qualidade e melhoria contínua."
            ),
            "rate": 175,
        },
        {
            "key": "nise",
            "name": "NISE",
            "role": "Assistente Virtual do Paciente",
            "origin": "Nise da Silveira",
            "represents": "Humanização, acolhimento e comunicação empática com pacientes",
            "activation": "Interação direta com pacientes via chatbot e canais de comunicação",
            "highlights": [
                "Chatbot Dr. Nise no Rocket.Chat para pacientes",
                "Linguagem acessível e empática",
                "Orientações sobre exames, medicações e autocuidado",
            ],
            "narration": (
                "Esta é a Nise. Ela é a voz humanizada do IntelliCare, "
                "conversando diretamente com pacientes de forma acolhedora e clara."
            ),
            "rate": 180,
        },
        {
            "key": "minerva",
            "name": "MINERVA",
            "role": "Gestão de Conhecimento Clínico",
            "origin": "Minerva - Deusa da Sabedoria",
            "represents": "Protocolos clínicos, diretrizes e base de conhecimento",
            "activation": "Consulta a protocolos, guidelines e evidências científicas",
            "highlights": [
                "Repositório de protocolos clínicos estruturados",
                "Busca semântica em diretrizes e evidências",
                "Integração com RAG da Florence",
            ],
            "narration": (
                "Esta é a Minerva. Ela guarda e organiza todo o conhecimento clínico, "
                "protocolos e diretrizes que fundamentam nossas decisões."
            ),
            "rate": 178,
        },
        {
            "key": "pierre",
            "name": "PIERRE",
            "role": "Pesquisa e Inovação",
            "origin": "Pierre Curie - Cientista",
            "represents": "Análise de dados, pesquisa clínica e descoberta de padrões",
            "activation": "Análises estatísticas, coortes e estudos observacionais",
            "highlights": [
                "Análise de coortes e tendências populacionais",
                "Identificação de padrões em dados clínicos",
                "Suporte a pesquisa e inovação baseada em dados",
            ],
            "narration": (
                "Este é o Pierre. Ele analisa grandes volumes de dados clínicos "
                "para descobrir padrões e gerar conhecimento científico."
            ),
            "rate": 176,
        },
    ]

    for agent in agents:
        slide = AgentProfileSlide(
            agent_name=agent["name"],
            role=agent["role"],
            origin=agent["origin"],
            represents=agent["represents"],
            activation=agent["activation"],
            highlights=agent["highlights"],
            narration=agent["narration"],
            image_path=_resolve_agent_image(agent["key"], image_style),
            secondary_image_path=(
                _resolve_agent_image(agent["key"], "cartoon")
                if image_style == "dual"
                else None
            ),
        )
        slide.narration_rate = agent["rate"]
        slide.deep_dive_content = agent.get("deep_dive", {
            "title": f"{agent['name']} - Exemplo de Atuação",
            "content": (
                "Pergunta típica:\n"
                f"- Como o {agent['name']} contribui nesta decisão?\n\n"
                "Resposta esperada:\n"
                "- Contexto objetivo\n"
                "- Recomendações acionáveis\n"
                "- Transparência sobre limites e fontes"
            ),
        })
        slides.append(slide)

    # ── Slide 10: Encerramento ──
    slide_final = MetricsSlide(
        title="Ecossistema IntelliCare",
        subtitle="Inteligência artificial coordenada para o cuidado em saúde",
        metrics=[
            {
                "label": "Agentes Especializados",
                "value": "9",
                "icon": "A",
                "description": "Wanda, Florence, Oswaldo, Zilda, Geralda, Donabedian, Nise, Minerva, Pierre",
            },
            {
                "label": "Pilares de Arquitetura",
                "value": "4",
                "icon": "P",
                "description": "Rules, Skills, MCPs, Subagents",
            },
            {
                "label": "Padrão de Saúde",
                "value": "FHIR",
                "icon": "F",
                "description": "Interoperabilidade HL7 R4",
            },
            {
                "label": "Visão Integrada",
                "value": "360\u00b0",
                "icon": "V",
                "description": "Clínica, gestão e território",
            },
        ],
        narration=(
            "Encerramos com uma visão integrada: nove agentes especializados, "
            "quatro pilares de arquitetura, interoperabilidade FHIR e uma visão "
            "trezentos e sessenta graus do cuidado. Eu coordeno esse ecossistema "
            "para gerar valor clínico, operacional e institucional."
        ),
    )
    slide_final.narration_rate = 180
    slide_final.deep_dive_content = {
        "title": "Mensagem Final para Stakeholders",
        "content": (
            "- Clínicos: decisão mais segura no ponto de cuidado\n"
            "- Gestores: melhor governança e qualidade assistencial\n"
            "- Técnicos: arquitetura modular para evolução contínua\n"
            "- Institucional: narrativa clara de impacto e confiança"
        ),
    }
    slides.append(slide_final)

    return slides
