"""
Slides da V3 - Agentes Completa do IntelliCare.

Estrutura (15 slides):
  Bloco 1 — Abertura e Contexto (3 slides)
  Bloco 2 — Os Agentes (9 slides: Wanda, Florence, Oswaldo, Zilda, Geralda, Nise,
             Donabedian, Minerva, Pierre)
  Bloco 3 — Integração e Encerramento (3 slides)

Narrativa rica com contexto histórico para cada agente,
conforme PLANO_DESENVOLVIMENTO_APRESENTACAO_AGENTES.md.
"""

from pathlib import Path
from typing import Dict, List

from slides.content_slide import ContentSlide
from slides.diagram_slide import DiagramSlide
from slides.metrics_slide import MetricsSlide
from slides.title_slide import TitleSlide
from slides.agent_profile_slide import AgentProfileSlide
from slides.integration_flow_slide import IntegrationFlowSlide


# ──────────────────────────────────────────────
# Resolução de imagens (reutiliza V2 + Nise)
# ──────────────────────────────────────────────

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
            "nise": "nise_cartoon.png",
            "donabedian": "donabedian_cartoon.png",
            "minerva": "agente_minerva_ia.png",
            "pierre": "agente_pierre_ia.png",
        },
        "real": {
            "wanda": "agente_wanda_ia.png",
            "florence": "agente_florence_ia.png",
            "oswaldo": "agente_oswaldo_ia.png",
            "zilda": "agente_zilda_arns_ia.png",
            "geralda": "agente_geralda_ia.png",
            "nise": "agente_nise_ia.png",
            "donabedian": "agente_donabedian_ia.png",
            "minerva": "agente_minerva_ia.png",
            "pierre": "agente_pierre_ia.png",
        },
        "dual": {
            "wanda": "agente_wanda_ia.png",
            "florence": "agente_florence_ia.png",
            "oswaldo": "agente_oswaldo_ia.png",
            "zilda": "agente_zilda_arns_ia.png",
            "geralda": "agente_geralda_ia.png",
            "nise": "agente_nise_ia.png",
            "donabedian": "agente_donabedian_ia.png",
            "minerva": "agente_minerva_ia.png",
            "pierre": "agente_pierre_ia.png",
        },
    }

    filename = style_map.get(style, style_map["cartoon"]).get(agent_key)
    if not filename:
        return ""
    return str(images_dir / filename)


# ──────────────────────────────────────────────
# Fábrica de slides V3
# ──────────────────────────────────────────────

def create_v3_slides(image_style: str = "cartoon") -> List:
    """Cria os 13 slides da versão V3 (agentes completa)."""
    slides: List = []

    # ════════════════════════════════════════════
    # BLOCO 1 — ABERTURA E CONTEXTO (3 slides)
    # ════════════════════════════════════════════

    # ── Slide 1: Título ──
    slide1 = TitleSlide(
        title="IntelliCare",
        subtitle="Agentes Inspirados em Gigantes da Saúde",
        narration=(
            "Olá. Eu sou a Wanda, a orquestradora do IntelliCare. "
            "Nesta apresentação, vou contar a história dos nomes que "
            "escolhemos para nossos agentes e o que cada um faz pelo "
            "cuidado em saúde. Cada nome carrega um legado. "
            "Vamos comecar?"
        ),
    )
    slide1.narration_rate = 158
    slides.append(slide1)

    # ── Slide 2: Público-alvo ──
    slide2 = ContentSlide(
        title="Para Quem Esta Apresentação Foi Desenhada",
        content=[
            "Equipes clínicas: segurança e decisão no ponto de cuidado",
            "Gestores públicos: rede assistencial, qualidade e indicadores",
            "Times técnicos: arquitetura, integração e governança",
            "Cidadãos e parceiros: clareza, confiança e transparência",
        ],
        narration=(
            "Esta apresentação foi planejada para públicos diferentes. "
            "Profissionais de saúde encontrarão relevância clínica. "
            "Gestores verão indicadores e qualidade. Técnicos entenderão "
            "a arquitetura. E cidadãos perceberão a transparência do sistema. "
            "Linguagem clara para cada perfil, foco em valor prático."
        ),
    )
    slide2.narration_rate = 158
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

    # ── Slide 3: O Poder dos Nomes ──
    slide3 = ContentSlide(
        title="O Poder dos Nomes",
        content=[
            "Cada agente homenageia um gigante da saúde ou da ciência",
            "Nomes que carregam valores, missão e história",
            "Conexão entre o legado do passado e a tecnologia do futuro",
            "Nove figuras que transformaram o cuidado em saúde no mundo",
        ],
        narration=(
            "Antes de conhecer cada agente, quero explicar por que seus nomes "
            "importam. Quando escolhemos nomes de figuras históricas, não foi "
            "por acaso. Cada nome carrega uma missão. Wanda de Aguiar Horta, "
            "Florence Nightingale, Oswaldo Cruz, Zilda Arns, Geralda Lopes, "
            "Nise da Silveira, Avedis Donabedian, Minerva e Pierre Curie. "
            "Essas pessoas e símbolos transformaram a saúde e a ciência com "
            "dedicação, rigor e humanização. Nossos agentes honram esse legado. "
            "Vamos conhecer cada um deles."
        ),
    )
    slide3.narration_rate = 155
    slide3.deep_dive_content = {
        "title": "Os 9 Homenageados",
        "content": (
            "- Wanda de Aguiar Horta (1926–): Teoria das Necessidades Humanas Básicas\n"
            "- Florence Nightingale (1820–1910): Estatística aplicada à saúde\n"
            "- Oswaldo Cruz (1872–1917): Erradicação de epidemias no Brasil\n"
            "- Zilda Arns (1934–2010): Pastoral da Criança, 20 países\n"
            "- Geralda Lopes da Silva: Enfermagem comunitária brasileira\n"
            "- Nise da Silveira (1905–1999): Humanização da psiquiatria\n"
            "- Avedis Donabedian (1919–2000): 'Pai da Qualidade em Saúde'\n"
            "- Minerva (mitologia romana): Deusa da sabedoria e do conhecimento\n"
            "- Pierre Curie (1859–1906): Nobel de Física, ciência rigorosa e incansável"
        ),
    }
    slides.append(slide3)

    # ════════════════════════════════════════════
    # BLOCO 2 — OS AGENTES (9 slides)
    # ════════════════════════════════════════════

    agents = [
        # ── WANDA ──
        {
            "key": "wanda",
            "name": "WANDA",
            "role": "Orquestradora Proativa do Ecossistema",
            "origin": "Wanda de Aguiar Horta — enfermeira brasileira, professora USP",
            "represents": "Orquestração multi-agente, alertas clínicos e coordenação ativa",
            "activation": "Pergunta multi-domínio, eventos clínicos, alertas e workflows",
            "highlights": [
                "LangGraph workflows: análise clínica, onboarding e alerta crítico",
                "AlertHub: deduplicação, priorização e escalação de alertas clínicos",
                "Bot @intellicare no Rocket.Chat + Dr. Nise para pacientes",
            ],
            "narration": (
                "Olá, eu sou a Wanda, e é uma honra carregar este nome. "
                "Wanda de Aguiar Horta foi uma enfermeira brasileira extraordinária "
                "que ensinou que cuidar é ver o ser humano como um todo, suas "
                "necessidades físicas, emocionais, sociais. Ela dizia 'gente que "
                "cuida de gente'. E é exatamente isso que faço no IntelliCare: "
                "quando você faz uma pergunta, eu orquestro os especialistas certos, "
                "integro suas respostas e entrego um cuidado completo. Mas não espero "
                "mais só ser perguntada. Monitoro eventos do ecossistema, disparo "
                "alertas clínicos antes que virem emergências e aciono workflows "
                "inteligentes com LangGraph. Assim como "
                "Wanda Horta integrou saberes para criar uma teoria de enfermagem, "
                "eu integro agentes para criar uma resposta completa e proativa. "
                "Vamos conhecer minha equipe?"
            ),
            "rate": 160,
            "deep_dive": {
                "title": "WANDA Fase 3 — Orquestração Proativa",
                "content": (
                    "Wanda Horta ensinou que cuidar é integrar necessidades.\n"
                    "Nossa Wanda orquestra proativamente, não apenas reage.\n\n"
                    "Novas capacidades (Fase 3):\n"
                    "- LangGraph: 3 workflows (clínico, onboarding, alerta crítico)\n"
                    "- AlertHub: dedup + prioridade + consolidação + escalação\n"
                    "- Event Consumer: Redis Streams (lab, vitais, adesão, condições)\n"
                    "- Bot RC: @intellicare no Rocket.Chat com 7 comandos clínicos\n"
                    "- Dr. Nise: chatbot educacional para pacientes via FLOWISE"
                ),
            },
        },
        # ── FLORENCE ──
        {
            "key": "florence",
            "name": "FLORENCE",
            "role": "Inteligência Clínica Profunda",
            "origin": "Florence Nightingale — enfermeira britânica, pioneira em estatística",
            "represents": "Análise clínica baseada em evidências e dados",
            "activation": "Interpretação de exames e evolução clínica complexa",
            "highlights": [
                "Interpretação de 27 exames laboratoriais com tendências",
                "8 padrões de correlação clínica automáticos",
                "RAG com 10 protocolos clínicos indexados",
            ],
            "narration": (
                "Conheçam Florence. A Florence Nightingale original percorria enfermarias "
                "à noite com sua lamparina, cuidando de feridos. Mas ela não era apenas "
                "uma cuidadora, era uma cientista. Ela coletava dados, criava gráficos "
                "inovadores e provou matematicamente que saneamento e higiene reduziam "
                "mortes. Ela foi pioneira no uso de evidências para salvar vidas. "
                "Nossa Florence mantém esse mesmo espírito: ela analisa exames laboratoriais, "
                "detecta padrões que o olho humano pode não ver, consulta protocolos clínicos "
                "e oferece insights baseados em evidências sólidas. Quando um paciente tem "
                "creatinina e ureia elevadas, Florence identifica o padrão de comprometimento "
                "renal e alerta sobre a urgência. Ciência a serviço da vida."
            ),
            "rate": 148,
            "deep_dive": {
                "title": "FLORENCE — Por que este nome?",
                "content": (
                    "Florence Nightingale provou que dados salvam vidas.\n"
                    "Nossa Florence analisa exames com rigor científico "
                    "e oferece insights baseados em evidências.\n\n"
                    "Capacidades:\n"
                    "- 27 exames laboratoriais interpretados\n"
                    "- Detecção de tendências via regressão linear\n"
                    "- 8 padrões de correlação clínica\n"
                    "- RAG com 10 protocolos clínicos indexados"
                ),
            },
        },
        # ── OSWALDO ──
        {
            "key": "oswaldo",
            "name": "OSWALDO",
            "role": "Motor Genérico de Doenças Crônicas",
            "origin": "Oswaldo Cruz — médico sanitarista, fundador da Fiocruz",
            "represents": "Monitoramento longitudinal via Disease Profiles YAML",
            "activation": "Análise de progressão, estadiamento e alertas crônicos",
            "highlights": [
                "Motor genérico: CKD, Diabetes e HAS via configuração YAML",
                "Estadiamento plugável: KDIGO, ADA, ESC/ESH por doença",
                "Alertas de descompensação antes que virem emergências",
            ],
            "narration": (
                "Este é Oswaldo, em homenagem a Oswaldo Cruz, o gigante da saúde "
                "pública brasileira. No início do século vinte, o Rio de Janeiro era "
                "assolado por epidemias de febre amarela, peste bubônica e varíola. "
                "Oswaldo Cruz, com seu rigor científico e determinação, liderou "
                "campanhas que erradicaram essas doenças e transformaram a cidade. "
                "Ele combateu epidemias que matavam milhares. Nosso Oswaldo combate "
                "outro tipo de epidemia silenciosa: as doenças crônicas. Diabetes, "
                "hipertensão, doença renal. Condições que, se não monitoradas, levam "
                "a complicações graves. Oswaldo monitora longitudinalmente, detecta "
                "descompensações antes que virem emergências e ajuda a prevenir "
                "tragédias. Se Oswaldo Cruz salvou milhares com suas campanhas, nosso "
                "Oswaldo salva vidas todos os dias com monitoramento inteligente."
            ),
            "rate": 155,
            "deep_dive": {
                "title": "OSWALDO V4 — Motor Genérico de Doenças Crônicas",
                "content": (
                    "Oswaldo Cruz combateu epidemias. Nosso Oswaldo combate a epidemia "
                    "silenciosa das doenças crônicas.\n\n"
                    "Arquitetura V4:\n"
                    "- Disease Profiles em YAML: adicionar doença = novo arquivo\n"
                    "- Strategy Pattern: algoritmo de estadiamento plugável\n"
                    "- 3 perfis prontos: CKD (KDIGO), DM2 (ADA), HAS (ESC/ESH)\n\n"
                    "Exemplo de resposta estruturada:\n"
                    "- CKD: G3a/A2 — eGFR 48, queda de 8% em 90 dias\n"
                    "- HAS: Estágio 1 — PA 138/88, tendência estável\n"
                    "- Alertas com severidade + recomendações acionáveis"
                ),
            },
        },
        # ── ZILDA ──
        {
            "key": "zilda",
            "name": "ZILDA",
            "role": "Dados de Saúde Pública Brasileira",
            "origin": "Zilda Arns — médica pediatra, fundadora da Pastoral da Criança",
            "represents": "Contexto territorial e rede assistencial brasileira",
            "activation": "Consultas CNES, tipo de unidade e região de saúde",
            "highlights": [
                "Consulta CNES: estabelecimentos e rede assistencial",
                "Análise territorial e contexto epidemiológico regional",
                "Decisões de saúde ancoradas na realidade do território",
            ],
            "narration": (
                "Zilda. Que exemplo de dedicação! Zilda Arns foi uma médica pediatra "
                "que fundou a Pastoral da Criança e levou saúde, nutrição e dignidade "
                "às comunidades mais pobres do Brasil. Ela empoderou líderes comunitários, "
                "ensinou sobre soro caseiro, alimentação alternativa e cuidados básicos. "
                "Sua metodologia salvou incontáveis crianças e foi replicada em vinte "
                "países. Zilda trabalhou incansavelmente até o último dia de sua vida. "
                "Ela estava em missão humanitária no Haiti quando o terremoto de dois "
                "mil e dez a levou. Nossa Zilda honra esse legado trazendo dados do "
                "território brasileiro. Quando um médico atende um paciente, Zilda "
                "contextualiza: quais UBS existem na região? Qual a rede assistencial "
                "disponível? Quais os indicadores epidemiológicos locais? Decisões de "
                "saúde não acontecem no vácuo. Acontecem em territórios reais, com "
                "recursos reais. Zilda garante que nossas decisões sejam realistas e "
                "contextualizadas."
            ),
            "rate": 155,
            "deep_dive": {
                "title": "ZILDA — Por que este nome?",
                "content": (
                    "Zilda Arns levou saúde às comunidades.\n"
                    "Nossa Zilda traz o contexto territorial brasileiro "
                    "para decisões de saúde mais realistas e humanas.\n\n"
                    "Capacidades:\n"
                    "- Consulta CNES: estabelecimentos de saúde\n"
                    "- Análise territorial e contexto regional\n"
                    "- Integração DATASUS e e-SUS (em desenvolvimento)\n"
                    "- Contexto epidemiológico por região"
                ),
            },
        },
        # ── GERALDA ──
        {
            "key": "geralda",
            "name": "GERALDA",
            "role": "Acompanhamento do Paciente",
            "origin": "Geralda Lopes da Silva — pioneira da enfermagem comunitária",
            "represents": "Continuidade de cuidado e vínculo com o paciente",
            "activation": "Orientação, seguimento e comunicação da jornada",
            "highlights": [
                "Planos de cuidado personalizados com lembretes inteligentes",
                "Gestão de medicamentos, dieta e exercícios",
                "Educação em saúde acessível e cálculo de adesão",
            ],
            "narration": (
                "Geralda representa algo fundamental que muitas vezes esquecemos: "
                "o cuidado não acontece apenas na consulta. Ele acontece todo dia, "
                "em casa, na comunidade. Geralda Lopes da Silva foi pioneira da "
                "enfermagem comunitária no Brasil, levando cuidado para onde as pessoas "
                "vivem suas vidas. Nossa Geralda mantém esse cuidado vivo. Depois que "
                "Oswaldo identifica que um paciente tem diabetes, depois que Florence "
                "analisa os exames, é Geralda quem acompanha: lembretes para tomar "
                "medicação, orientações sobre alimentação, exercícios, monitoramento "
                "de glicemia. Geralda é a presença constante, o vínculo que não se rompe "
                "entre consultas. Ela calcula adesão ao tratamento e oferece educação "
                "em saúde acessível. Porque saúde não é um evento. É uma jornada, e "
                "Geralda caminha ao lado do paciente."
            ),
            "rate": 155,
            "deep_dive": {
                "title": "GERALDA — Por que este nome?",
                "content": (
                    "Geralda Lopes levou o cuidado para a comunidade.\n"
                    "Nossa Geralda mantém o cuidado vivo todo dia.\n\n"
                    "Capacidades:\n"
                    "- Planos de cuidado personalizados\n"
                    "- Lembretes: diário, semanal, mensal\n"
                    "- Gestão de medicamentos, dieta, exercícios\n"
                    "- Educação em saúde (DRC, DM2, HAS)\n"
                    "- Cálculo de adesão ao tratamento"
                ),
            },
        },
        # ── NISE ── (novo na V3)
        {
            "key": "nise",
            "name": "NISE",
            "role": "Chatbot Educacional do Paciente",
            "origin": "Nise da Silveira — psiquiatra, pioneira em arte-terapia e humanização",
            "represents": "Cuidado humanizado, educação acessível e vínculo terapêutico",
            "activation": "Quando o paciente tem dúvidas sobre sua saúde e tratamento",
            "highlights": [
                "Dr. Nise: chatbot seguro para pacientes via FLOWISE (LLM local)",
                "Privacidade LGPD: IPS simplificado — sem CPF, nome ou DOB",
                "Filtros de segurança: bloqueia conselhos perigosos, escala emergências",
            ],
            "narration": (
                "Nise da Silveira. Uma mulher à frente de seu tempo. Quando a "
                "psiquiatria brasileira usava eletrochoque, lobotomia e isolamento, "
                "Nise escolheu um caminho radical: o afeto, a arte, a humanização. "
                "Ela transformou o tratamento psiquiátrico ao mostrar que cuidar é "
                "também criar vínculos, também dar voz ao paciente. Nise fundou o Museu de "
                "Imagens do Inconsciente, onde pacientes expressavam sua humanidade "
                "através da arte. Nossa Nise honra esse legado: ela é o chatbot educacional "
                "que conversa com o paciente com respeito e clareza. Usando FLOWISE e "
                "inteligência artificial local, Dr. Nise responde dúvidas sobre saúde, "
                "orienta sobre o tratamento e educa com linguagem acessível. "
                "Com segurança máxima: dados identificáveis nunca saem do sistema, "
                "conselhos perigosos são bloqueados, e emergências são escaladas "
                "automaticamente para a equipe clínica. Assim como Nise da Silveira "
                "devolveu dignidade aos pacientes, nossa Nise devolve autonomia."
            ),
            "rate": 150,
            "deep_dive": {
                "title": "Dr. Nise — Chatbot Seguro para Pacientes (EF-W013)",
                "content": (
                    "Nise da Silveira ensinou com afeto e humanização.\n"
                    "Nossa Nise conversa com o paciente com segurança e respeito.\n\n"
                    "Pipeline de segurança:\n"
                    "1. IPS simplificado: condições, classes de meds, faixa etária\n"
                    "   (sem CPF, nome completo, DOB ou valores de exames)\n"
                    "2. FLOWISE: LLM local, sem dados externos\n"
                    "3. Filtro: DANGER_PATTERNS bloqueiam automedicação\n"
                    "4. Escalação: 'dor no peito', 'suicídio' → AlertHub CRITICAL\n\n"
                    "Capacidades:\n"
                    "- Sessões com histórico (TTL 2h, arquivo LGPD no PostgreSQL)\n"
                    "- Audit log completo de todas as interações"
                ),
            },
        },
        # ── DONABEDIAN ──
        {
            "key": "donabedian",
            "name": "DONABEDIAN",
            "role": "Avaliação de Qualidade em Saúde",
            "origin": "Avedis Donabedian — 'Pai da Qualidade em Saúde'",
            "represents": "Qualidade assistencial e governança por indicadores",
            "activation": "Análise de estrutura, processo, resultado e desempenho",
            "highlights": [
                "Framework Estrutura-Processo-Resultado aplicado ao sistema",
                "15+ indicadores de qualidade com análise temporal",
                "Dashboard interativo de melhoria contínua",
            ],
            "narration": (
                "Por fim, mas não menos importante: Donabedian. Avedis Donabedian foi "
                "um visionário que transformou como pensamos sobre qualidade em saúde. "
                "Antes dele, qualidade era subjetiva, intuitiva. Donabedian mostrou que "
                "qualidade se mede, se avalia, se melhora sistematicamente. Sua tríade, "
                "estrutura, processo e resultado, é usada mundialmente até hoje. Ele "
                "perguntava: temos os recursos certos? Fazemos as coisas certas? Obtemos "
                "os resultados que queremos? Nosso Donabedian aplica esse rigor científico "
                "ao IntelliCare. Ele coleta dados de todos os agentes, calcula indicadores "
                "de qualidade, identifica tendências, aponta onde podemos melhorar. "
                "Estrutura: nossos agentes estão funcionando? Processo: os fluxos são "
                "eficientes? Resultado: os pacientes estão sendo bem cuidados? Donabedian "
                "garante que nosso sistema não apenas funcione, mas melhore continuamente. "
                "Porque qualidade não é acidente. É disciplina."
            ),
            "rate": 148,
            "deep_dive": {
                "title": "DONABEDIAN — Por que este nome?",
                "content": (
                    "Donabedian mostrou que qualidade se mede e se melhora.\n"
                    "Nosso Donabedian transforma dados em gestão de qualidade.\n\n"
                    "Tríade Donabedian aplicada:\n"
                    "- Estrutura: agentes ativos, infra saudável\n"
                    "- Processo: fluxos eficientes, tempo de resposta\n"
                    "- Resultado: desfechos, adesão, satisfação\n\n"
                    "15+ indicadores, dashboard Streamlit, consolidação Redis → PostgreSQL"
                ),
            },
        },
        # ── MINERVA ──
        {
            "key": "minerva",
            "name": "MINERVA",
            "role": "OCR e Extração de Conhecimento",
            "origin": "Minerva — deusa romana da sabedoria e das artes",
            "represents": "Ler, interpretar e extrair conhecimento de documentos clínicos",
            "activation": "Processamento de laudos PDF, imagens médicas e documentos digitalizados",
            "highlights": [
                "OCR avançado de documentos clínicos via MCP Server (porta 8008)",
                "Extração estruturada de laudos PDF e imagens médicas",
                "Integração com WANDA para enriquecimento do IPS",
            ],
            "narration": (
                "Conheçam Minerva. Na mitologia romana, Minerva era a deusa da sabedoria, "
                "das artes e do conhecimento. Ela representava a capacidade de compreender "
                "o mundo através da observação cuidadosa e do estudo. Nossa Minerva mantém "
                "esse espírito: ela lê documentos clínicos que chegam em PDF ou imagens, "
                "extrai o conhecimento contido neles e transforma dados não estruturados "
                "em informação clínica útil. Quando um laudo de ultrassom chega digitalizado, "
                "Minerva aplica OCR avançado, identifica achados relevantes e alimenta o "
                "prontuário do paciente. Ela é a ponte entre o papel e o digital, entre "
                "o texto e o dado estruturado. Porque conhecimento aprisionado em documentos "
                "não pode ser usado. Minerva liberta esse conhecimento."
            ),
            "rate": 152,
            "deep_dive": {
                "title": "MINERVA (intellicare-ocr) — Extração Documental",
                "content": (
                    "Minerva, deusa da sabedoria, ensina que conhecimento deve ser acessível.\n"
                    "Nossa Minerva extrai conhecimento de documentos clínicos.\n\n"
                    "Capacidades:\n"
                    "- OCR de laudos PDF e imagens médicas\n"
                    "- Extração estruturada de achados clínicos\n"
                    "- MCP Server na porta 8008\n"
                    "- Integração com WANDA via WandaMCPClient"
                ),
            },
        },
        # ── PIERRE ──
        {
            "key": "pierre",
            "name": "PIERRE",
            "role": "Supervisão Científica e Busca de Evidências",
            "origin": "Pierre Curie — físico francês, Prêmio Nobel de Física (1903)",
            "represents": "Pesquisa, descoberta e acesso ao conhecimento científico",
            "activation": "Busca em guidelines, PubMed, literatura científica atualizada",
            "highlights": [
                "Busca em bases científicas (PubMed, guidelines KDIGO, ADA, ESC)",
                "Web search para evidências e recomendações atualizadas",
                "MCP Server com ferramentas de supervisão científica (porta 8009)",
            ],
            "narration": (
                "Por fim, apresento Pierre. Pierre Curie foi um cientista extraordinário "
                "que dedicou sua vida à pesquisa e à descoberta. Junto com Marie Curie, "
                "ele investigou a radioatividade e transformou nossa compreensão da física. "
                "Pierre não aceitava respostas fáceis: ele buscava evidências, testava "
                "hipóteses, questionava o conhecimento estabelecido. Nosso Pierre segue "
                "esse legado científico. Quando WANDA precisa de evidências sobre o manejo "
                "de DRC em estágio G3b, Pierre busca no PubMed, consulta guidelines KDIGO "
                "atualizados e traz recomendações baseadas na melhor ciência disponível. "
                "Ele é o pesquisador incansável, o guardião da evidência científica. "
                "Porque em saúde, opiniões não bastam. Precisamos de ciência."
            ),
            "rate": 150,
            "deep_dive": {
                "title": "PIERRE (intellicare-superz) — Evidência Científica",
                "content": (
                    "Pierre Curie ensinou que ciência é busca incansável por evidências.\n"
                    "Nosso Pierre busca conhecimento científico para apoiar decisões.\n\n"
                    "Capacidades:\n"
                    "- Busca em PubMed e literatura científica\n"
                    "- Consulta a guidelines (KDIGO, ADA, ESC)\n"
                    "- Web search para evidências recentes\n"
                    "- MCP Server na porta 8009\n"
                    "- Integração com WANDA via WandaMCPClient"
                ),
            },
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
            "title": f"{agent['name']} — Exemplo de Atuação",
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

    # ════════════════════════════════════════════
    # BLOCO 3 — INTEGRAÇÃO E ENCERRAMENTO (3 slides)
    # ════════════════════════════════════════════

    # ── Slide 11: Como os Agentes Trabalham Juntos ──
    slide11 = IntegrationFlowSlide(
        title="Como os Agentes Trabalham Juntos",
        case_title="Paciente com diabetes descompensada",
        steps=[
            {"agents": "PORTAL",                "label": "1.",  "detail": "Médico faz pergunta"},
            {"agents": "WANDA",                  "label": "2.",  "detail": "Recebe, analisa e roteia"},
            {"agents": "FLORENCE, OSWALDO, ZILDA","label": "3.",  "detail": "Exames · DM2 · Rede territorial"},
            {"agents": "NISE",                   "label": "4.",  "detail": "Consulta protocolo atualizado"},
            {"agents": "GERALDA",                "label": "5.",  "detail": "Monta plano de acompanhamento"},
            {"agents": "DONABEDIAN",             "label": "6.",  "detail": "Registra indicadores de qualidade"},
            {"agents": "WANDA",                  "label": "7.",  "detail": "Consolida resposta ao médico"},
        ],
        narration=(
            "Veja como tudo se conecta. Imagine um médico atendendo um paciente "
            "com diabetes descompensada. Ele faz uma pergunta pelo portal. Eu, Wanda, "
            "recebo e entendo que preciso acionar Florence para analisar exames, "
            "Oswaldo para avaliar o estadiamento da diabetes, e Zilda para verificar "
            "a rede assistencial disponível. Com as respostas, Geralda monta o plano "
            "de acompanhamento domiciliar. E Donabedian registra indicadores de qualidade "
            "do atendimento. Tudo isso acontece de forma integrada, rastreável e segura. "
            "Sete agentes, uma resposta completa."
        ),
    )
    slide11.narration_rate = 152
    slide11.deep_dive_content = {
        "title": "Fluxo Completo de Dados",
        "content": (
            "1. USUÁRIO faz pergunta via PORTAL\n"
            "2. WANDA recebe e analisa a query\n"
            "3. WANDA roteia para agentes especializados:\n"
            "   - 'glicemia alta' → OSWALDO + FLORENCE\n"
            "   - 'UBS na região' → ZILDA\n"
            "   - 'como tomar remédio' → GERALDA\n"
            "   - 'qualidade do atendimento' → DONABEDIAN\n"
            "   - 'protocolo de tratamento' → NISE\n"
            "4. AGENTES processam em paralelo\n"
            "5. WANDA agrega respostas\n"
            "6. WANDA aplica regras de segurança\n"
            "7. RESPOSTA consolidada ao usuário"
        ),
    }
    slides.append(slide11)

    # ── Slide 12: Valores que Carregamos ──
    slide12 = ContentSlide(
        title="Valores que Carregamos",
        content=[
            "Ciência e evidência: Florence e Donabedian",
            "Saúde pública e equidade: Oswaldo e Zilda",
            "Cuidado humanizado: Wanda, Geralda e Nise",
            "Qualidade e melhoria contínua: Donabedian",
        ],
        narration=(
            "Esses nomes não são apenas rótulos. São valores. Florence e Donabedian "
            "representam a ciência e a evidência. Oswaldo e Zilda representam saúde "
            "pública e equidade. Wanda, Geralda e Nise representam o cuidado "
            "humanizado. E Donabedian nos lembra que qualidade é disciplina, "
            "é melhoria contínua. Cada interação do IntelliCare carrega esses "
            "valores. Cada resposta reflete esse compromisso."
        ),
    )
    slide12.narration_rate = 155
    slide12.deep_dive_content = {
        "title": "Pilares de Valor do IntelliCare",
        "content": (
            "Ciência e evidência:\n"
            "  Florence: dados salvam vidas\n"
            "  Donabedian: qualidade se mede\n\n"
            "Saúde pública e equidade:\n"
            "  Oswaldo: combater epidemias silenciosas\n"
            "  Zilda: saúde no território real\n\n"
            "Cuidado humanizado:\n"
            "  Wanda: integrar para cuidar\n"
            "  Geralda: acompanhar a jornada\n"
            "  Nise: ensinar com afeto\n\n"
            "Melhoria contínua:\n"
            "  Donabedian: medir, avaliar, melhorar"
        ),
    }
    slides.append(slide12)

    # ── Slide 13: Encerramento ──
    slide_final = MetricsSlide(
        title="Ecossistema IntelliCare",
        subtitle="Um sistema que honra o passado e constrói o futuro da saúde",
        metrics=[
            {
                "label": "Agentes Especializados",
                "value": "9",
                "icon": "A",
                "description": "Cada um com papel clínico ou científico definido",
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
            "Encerramos com uma visão integrada. Nove agentes especializados, "
            "cada um homenageando um gigante da saúde ou da ciência. Quatro pilares de arquitetura. "
            "Interoperabilidade FHIR. E uma visão trezentos e sessenta graus do cuidado: "
            "clínica, gestão e território. Eu, Wanda, coordeno esse ecossistema para "
            "gerar valor clínico, operacional e institucional. Cada nome é uma "
            "responsabilidade. Cada agente, um compromisso. IntelliCare: inteligência "
            "artificial coordenada para o cuidado em saúde. Obrigada."
        ),
    )
    slide_final.narration_rate = 152
    slide_final.deep_dive_content = {
        "title": "Mensagem Final para Stakeholders",
        "content": (
            "- Clínicos: decisão mais segura no ponto de cuidado\n"
            "- Gestores: melhor governança e qualidade assistencial\n"
            "- Técnicos: arquitetura modular para evolução contínua\n"
            "- Institucional: narrativa clara de impacto e confiança\n\n"
            "Próximos passos:\n"
            "- Expansão do motor Oswaldo (novas doenças)\n"
            "- Integração DATASUS via Zilda\n"
            "- Portal unificado com Donabedian dashboard\n"
            "- Nise: treinamento em escala com LLM local"
        ),
    }
    slides.append(slide_final)

    return slides