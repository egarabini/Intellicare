"""
Slides da V1 - Visão Geral do IntelliCare.
"""

from typing import List
from slides.title_slide import TitleSlide
from slides.content_slide import ContentSlide
from slides.diagram_slide import DiagramSlide
from slides.metrics_slide import MetricsSlide


def create_v1_slides() -> List:
    """
    Cria os 5 slides da V1 - Visão Geral.
    
    Returns:
        Lista de slides
    """
    slides = []
    
    # Slide 1: Título
    slide1 = TitleSlide(
        title="IntelliCare",
        subtitle="Sistema de Saúde Inteligente com IA",
        narration="""
        Olá! Eu sou a Wanda, e vou apresentar o IntelliCare,
        um sistema revolucionário de saúde que integra inteligência
        artificial com múltiplos domínios hospitalares e governamentais.
        """
    )
    slide1.narration_rate = 160
    slides.append(slide1)

    # Slide 2: O Problema
    slide2 = ContentSlide(
        title="O Desafio da Saúde no Brasil",
        content=[
            "❌ Dados isolados em silos",
            "❌ Sem integração Hospital ↔ Governo",
            "❌ Processos manuais e lentos",
            "❌ Falta de visão 360° do paciente"
        ],
        narration="""
        Hoje, os sistemas de saúde enfrentam grandes desafios.
        Os dados estão isolados em diferentes sistemas,
        não há integração entre hospital e governo,
        e os profissionais não têm uma visão completa do paciente.
        """
    )

    # Adiciona Deep Dive com detalhes da arquitetura
    slide2.deep_dive_content = {
        "title": "Detalhes da Arquitetura IntelliCare",
        "content": """🏗️ Microservices em Python + FastAPI

• API Gateway com autenticação JWT
• Serviços independentes por domínio
• Message Queue (RabbitMQ) para eventos
• Cache distribuído (Redis)
• Banco de dados PostgreSQL

🔗 Integrações:
• FHIR Server (HL7 FHIR R4)
• RNDS (Rede Nacional de Dados em Saúde)
• Careplanner (Sistema Hospitalar)

🤖 IA e Agentes:
• LangGraph para orquestração
• LangChain para ferramentas
• OpenAI GPT-4 para raciocínio
• MCP (Model Context Protocol)"""
    }

    slide2.narration_rate = 155
    slides.append(slide2)

    # Slide 3: A Solução - Wanda
    diagram = """
    ┌─────────────────────────────────────┐
    │      WANDA ORCHESTRATOR             │
    │   (LangGraph + LangChain)           │
    └─────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │  FHIR  │  │  RNDS  │  │ Care-  │
    │ Server │  │  API   │  │planner │
    └────────┘  └────────┘  └────────┘
    """
    
    slide3 = DiagramSlide(
        title="Wanda: Orquestrador Inteligente",
        diagram=diagram,
        narration="""
        A Wanda é um orquestrador inteligente que integra
        múltiplos domínios: Hospital, Governo e Clínico.
        Ela entende perguntas em linguagem natural e
        decide automaticamente quais sistemas consultar.
        """
    )
    slide3.narration_rate = 158
    slides.append(slide3)

    # Slide 4: Capacidades
    slide4 = MetricsSlide(
        title="O que a Wanda Sabe Fazer",
        metrics=[
            {"label": "Ferramentas Integradas", "value": "13", "icon": "🔧"},
            {"label": "Sistemas Conectados", "value": "5", "icon": "🔗"},
            {"label": "Tempo Médio", "value": "2.6s", "icon": "⚡"},
            {"label": "Taxa de Sucesso", "value": "100%", "icon": "✅"}
        ],
        narration="""
        A Wanda integra 13 ferramentas diferentes,
        conecta 5 sistemas distintos,
        responde em média em 2.6 segundos,
        e tem 100 por cento de taxa de sucesso nos testes.
        """
    )
    slide4.narration_rate = 162
    slides.append(slide4)

    # Slide 5: Demonstração
    demo_text = """
    Query: "O paciente João Silva está internado?
            Se sim, ele tem cadastro no governo?"
    
    Wanda:
    ✓ Analisando query...
    ✓ Consultando Careplanner (Hospital)...
    ✓ Consultando RNDS (Governo)...
    ✓ Cruzando informações...
    
    Resultado:
    🏥 Hospital: João Silva INTERNADO
       Setor: UTI, Leito: 101
    
    🇧🇷 Governo: João Silva CADASTRADO
       CNS: 123456789012345
    """
    
    slide5 = DiagramSlide(
        title="Demonstração: Raciocínio Multi-Domínio",
        diagram=demo_text,
        narration="""
        Agora vou mostrar o raciocínio multi-domínio em ação.
        Vou fazer uma pergunta que requer consultar dois sistemas diferentes:
        o hospital e o governo. A Wanda cruza as informações automaticamente
        e retorna uma resposta integrada.
        """
    )
    slide5.narration_rate = 150
    slides.append(slide5)

    return slides

