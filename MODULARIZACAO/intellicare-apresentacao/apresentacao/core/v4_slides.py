import pygame
from core.overlay import TextOverlay

class Slide:
    """Classe de Slide compatível com o PresentationEngine."""
    def __init__(self, title, subtitle, content, narration, speaker="wanda", show_graph=False):
        self.title = title
        self.subtitle = subtitle
        self.content = content
        self.narration_text = narration
        self.speaker = speaker
        self.show_graph_viz = show_graph
        self.narration_rate = 160
        self.has_played_narration = False
        self.current_overlay = None
        
        # Deep dive content (optional)
        self.deep_dive_title = None
        self.deep_dive_content = None

    def set_deep_dive(self, title, content):
        self.deep_dive_title = title
        self.deep_dive_content = content

    def has_deep_dive(self):
        return self.deep_dive_title is not None

    def open_deep_dive(self):
        if self.has_deep_dive():
            self.current_overlay = TextOverlay(self.deep_dive_title, self.deep_dive_content)

    def close_deep_dive(self):
        if self.current_overlay:
            self.current_overlay.close()

    def update(self, delta_time, slide_time):
        if self.current_overlay:
            finished = self.current_overlay.update(delta_time)
            if finished and self.current_overlay.is_closing:
                self.current_overlay = None

    def render(self, screen, theme, fonts, slide_time):
        # Título
        title_surf = fonts["title"].render(self.title, True, theme["primary"])
        screen.blit(title_surf, (50, 50))
        
        # Subtítulo
        if self.subtitle:
            sub_surf = fonts["subtitle"].render(self.subtitle, True, theme["text_secondary"])
            screen.blit(sub_surf, (50, 150))
            
        # Conteúdo (Bullet points)
        y_offset = 250
        for line in self.content:
            text_surf = fonts["content"].render(f"• {line}", True, theme["text"])
            screen.blit(text_surf, (80, y_offset))
            y_offset += 60
            
        # Overlay (Deep Dive)
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)

def create_v4_presentation(engine):
    # Slide 1: Introdução (Wanda)
    s1 = Slide(
        title="IntelliCare V4",
        subtitle="De Monólito para Ecossistema de Agentes",
        content=[
            "Evolução da Arquitetura",
            "Inteligência Distribuída",
            "Orquestração Cognitiva"
        ],
        narration=(
            "Olá. Eu sou a Wanda. Bem-vindos à nova era do IntelliCare. "
            "Hoje vou mostrar como deixamos de ser um sistema monolítico rígido para nos tornarmos um ecossistema vivo de agentes inteligentes."
        ),
        speaker="wanda"
    )
    engine.add_slide(s1)

    # Slide 2: Arquitetura LangGraph (Wanda + Visual 3D)
    s2 = Slide(
        title="O Cérebro: LangGraph",
        subtitle="Supervisor & Workers",
        content=[
            "Wanda como Supervisor (Router)",
            "Delegação por Intenção",
            "Memória Persistente (Checkpoints)"
        ],
        narration=(
            "Esta é a minha nova estrutura mental. Eu atuo como um Supervisor no padrão LangGraph. "
            "Eu não tento fazer tudo sozinha. Eu entendo o que você precisa e delego para especialistas, como o Oswaldo ou a Florence."
        ),
        speaker="wanda",
        show_graph=True  # Ativa visualização 3D
    )
    engine.add_slide(s2)

    # Slide 3: Oswaldo (Voz Masculina/Grave)
    s3 = Slide(
        title="Oswaldo: Agente de Crônicos",
        subtitle="Monitoramento Longitudinal",
        content=[
            "Especialista em Diabetes e Renal",
            "Análise de Tendências (IPS Brasil)",
            "Detecção Precoce de Riscos"
        ],
        narration=(
            "Muito prazer. Eu sou o Oswaldo. "
            "Diferente de um algoritmo simples, eu analiso o histórico do paciente. "
            "Eu monitoro a tendência da creatinina e da hemoglobina glicada para evitar complicações antes que elas aconteçam."
        ),
        speaker="oswaldo"
    )
    engine.add_slide(s3)

    # Slide 4: Donabedian (Voz Masculina/Autoritária)
    s4 = Slide(
        title="Donabedian: Qualidade",
        subtitle="Estrutura, Processo e Resultado",
        content=[
            "Auditoria de Protocolos em Tempo Real",
            "Segurança do Paciente (Patient Safety)",
            "Governança Clínica"
        ],
        narration=(
            "Aqui é o Donabedian. "
            "Na saúde, confiança é bom, mas controle é essencial. "
            "Minha função é garantir que cada passo da jornada clínica siga rigorosamente os protocolos de segurança e qualidade."
        ),
        speaker="donabedian"
    )
    engine.add_slide(s4)

    # Slide 5: Encerramento (Wanda)
    s5 = Slide(
        title="Interoperabilidade Real",
        subtitle="Conectando o Cuidado",
        content=[
            "Nativo em FHIR R4",
            "Integrado à RNDS",
            "Terminologias Padrão (SNOMED, CID, LOINC)"
        ],
        narration=(
            "Para finalizar: nós falamos a língua da saúde. "
            "Nossa comunicação é nativa em FHIR e integrada à RNDS. "
            "Isso é o IntelliCare V4: Inteligência, Segurança e Conexão."
        ),
        speaker="wanda"
    )
    engine.add_slide(s5)