# 📋 PLANO DE DESENVOLVIMENTO - APRESENTAÇÃO DOS AGENTES INTELLICARE

**Data:** 16/02/2026  
**Objetivo:** Desenvolver apresentação completa dos agentes do IntelliCare, com foco na origem dos nomes, importância histórica e função dentro do sistema  
**Responsável:** Preparação para apresentação do projeto

---

## 📚 ÍNDICE

1. [Situação Atual do Sistema](#1-situação-atual-do-sistema)
2. [Status da Apresentação](#2-status-da-apresentação)
3. [Pesquisa Histórica dos Agentes](#3-pesquisa-histórica-dos-agentes)
4. [Arquitetura e Integração](#4-arquitetura-e-integração)
5. [Plano de Desenvolvimento](#5-plano-de-desenvolvimento)
6. [Roteiro Detalhado por Agente](#6-roteiro-detalhado-por-agente)

---

## 1. SITUAÇÃO ATUAL DO SISTEMA

### 1.1 Visão Geral

O **IntelliCare** é uma plataforma modular de saúde digital com **7 agentes especializados** + módulos de infraestrutura, seguindo uma **arquitetura LEGO** onde cada componente pode funcionar independentemente ou integrado ao ecossistema.

### 1.2 Agentes Principais - Status de Implementação

| Agente | Homenagem | Status | Cobertura Testes | Porta API |
|--------|-----------|--------|------------------|-----------|
| **WANDA** | Wanda de Aguiar Horta | ✅ Completo | 93% (69 testes) | 8007 |
| **FLORENCE** | Florence Nightingale | 🟡 Funcional | ~50% | 8002 |
| **OSWALDO** | Oswaldo Cruz | ✅ Completo | 85% (127 testes) | 8001 |
| **ZILDA** | Zilda Arns | 🟡 Funcional | 95% (68 testes) | 8003 |
| **GERALDA** | Geralda Lopes da Silva | ✅ Completo | 96% (108 testes) | 8006 |
| **NISE** | Nise da Silveira | 🟡 Funcional | - | 8000 |
| **DONABEDIAN** | Avedis Donabedian | ✅ Completo | 80% (277 testes) | 8004 |

**Legenda:**
- ✅ Completo: Produção ready
- 🟡 Funcional: Core features implementadas, algumas pendências

### 1.3 Módulos de Infraestrutura

| Módulo | Função | Status |
|--------|--------|--------|
| **intellicare-core** | Biblioteca base compartilhada | ✅ |
| **intellicare-auth** | Autenticação com Keycloak | ✅ |
| **intellicare-comunicacao** | Chat e videoconferência | ✅ |
| **intellicare-portal** | Dashboard unificado | ✅ |

### 1.4 Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                      USUÁRIOS E STAKEHOLDERS                     │
│          (Equipes Clínicas, Gestores, Técnicos, Cidadãos)      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   INTELLICARE-PORTAL │
                    │   Dashboard Unificado │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       WANDA          │
                    │   Orquestradora      │
                    │   (Query Router)     │
                    └──────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │FLORENCE │          │ OSWALDO │          │  ZILDA  │
    │Clínica  │          │Crônicos │          │Dados BR │
    │Profunda │          │         │          │         │
    └─────────┘          └─────────┘          └─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │                      │
                    ▼                      ▼
               ┌─────────┐          ┌────────────┐
               │GERALDA  │          │DONABEDIAN  │
               │Acompanh.│          │Qualidade   │
               └─────────┘          └────────────┘
                    │
                    ▼
               ┌─────────┐
               │  NISE   │
               │Educação │
               └─────────┘
```

### 1.5 Princípios da Arquitetura LEGO

✅ **Modularidade**: Cada agente funciona independentemente  
✅ **Padronização**: APIs REST com contratos LEGO (`/api/v1/health`, `/api/v1/info`)  
✅ **Interoperabilidade**: Comunicação via FHIR R4  
✅ **Event-Driven**: RabbitMQ/Redis para eventos assíncronos  
✅ **Separação de Dados**: Schemas operacional e analítico  
✅ **Comercialização**: Cada módulo pode ser vendido separadamente

---

## 2. STATUS DA APRESENTAÇÃO

### 2.1 Implementação Atual

A apresentação já possui uma base sólida implementada em Python com Pygame:

**✅ Infraestrutura Completa:**
- Engine de apresentação (Pygame, 60 FPS)
- Sistema de slides (5 tipos: Title, Content, Diagram, Metrics, Base)
- Narração TTS (online com OpenAI e offline com pyttsx3)
- Controles interativos (ESPAÇO, BACKSPACE, R, M, D, P, ESC)
- Animações suaves e transições
- Temas (dark/light)

**✅ Versões Disponíveis:**

#### V1 - Visão Geral (5 slides)
1. IntelliCare - Título
2. O Desafio da Saúde no Brasil
3. Wanda: Orquestrador Inteligente
4. O que a Wanda Sabe Fazer
5. Demonstração: Raciocínio Multi-Domínio

#### V2 - Agentes (10 slides)
1. IntelliCare - Título
2. Para Quem Esta Apresentação Foi Desenhada
3. WANDA - Orquestradora Clínica Inteligente
4. FLORENCE - Inteligência Clínica Profunda
5. OSWALDO - Monitoramento de Doenças Crônicas
6. ZILDA - Dados de Saúde Brasileira
7. GERALDA - Acompanhamento do Paciente
8. DONABEDIAN - Qualidade em Saúde
9. (NISE não incluída ainda)
10. Encerramento - Ecossistema Coordenado

### 2.2 Executar a Apresentação

```bash
cd apresentacao

# V1 - Visão Geral
python main.py --versao v1_visao_geral --voz offline

# V2 - Galeria de Agentes
python main.py --versao v2_agentes --voz offline

# V2 com imagens reais dos agentes históricos
python main.py --versao v2_agentes --agente-imagem real --voz offline

# V2 com transição real -> cartoon
python main.py --versao v2_agentes --agente-imagem dual --voz offline
```

### 2.3 Fases de Desenvolvimento

| Fase | Status | Descrição |
|------|--------|-----------|
| **Fase 1** | ✅ 100% | Protótipo Terminal |
| **Fase 2** | ✅ 100% | MVP Pygame |
| **Fase 3** | 📋 Preparada | Teste com Stakeholders |
| **Fase 4** | ⏸️ Aguardando | TTS Inteligente |
| **Fase 5** | ⏸️ Aguardando | Visualizações 3D |
| **Fase 6** | ⏸️ Aguardando | Interatividade Avançada |
| **Fase 7** | ⏸️ Aguardando | Polimento Final |

---

## 3. PESQUISA HISTÓRICA DOS AGENTES

### 3.1 WANDA - Wanda de Aguiar Horta 🇧🇷

**Quem foi:**
- **Nome completo:** Wanda de Aguiar Horta
- **Nascimento:** 11 de agosto de 1926
- **Nacionalidade:** Brasileira
- **Profissão:** Enfermeira, professora e teórica de enfermagem

**Importância Histórica:**
- Criadora da **Teoria das Necessidades Humanas Básicas** (1979)
- Uma das primeiras teorias de enfermagem desenvolvidas no Brasil
- Revolucionou a enfermagem brasileira ao sistematizar o cuidado
- Professora na Escola de Enfermagem da USP
- Baseou sua teoria na obra de Maslow e João Mohana

**Legado:**
- Introduziu o conceito de "gente que cuida de gente"
- Enfoque no ser humano como integral (biopsicossocial)
- Processo de enfermagem estruturado em 6 etapas
- Classificação de necessidades humanas básicas
- Referência fundamental na formação de enfermeiros no Brasil

**Por que escolhemos este nome:**
> "Wanda Horta ensinou que cuidar é integrar, é ver o todo, é orquestrar necessidades. Nossa Wanda faz exatamente isso: integra especialistas, orquestra respostas e cuida do paciente como um todo."

**Função no Sistema:**
- **Orquestradora Inteligente** do ecossistema IntelliCare
- Recebe perguntas e roteia para os agentes especializados
- Agrega múltiplas respostas em uma síntese coerente
- Aplica regras de segurança (IPS-First, anti-fabricação, interações medicamentosas)
- Ponto de entrada único para usuários

---

### 3.2 FLORENCE - Florence Nightingale 🇬🇧

**Quem foi:**
- **Nome completo:** Florence Nightingale
- **Nascimento:** 12 de maio de 1820 em Florença, Itália
- **Falecimento:** 13 de agosto de 1910 (90 anos) em Londres
- **Nacionalidade:** Britânica
- **Profissão:** Enfermeira, estatística e reformadora social

**Importância Histórica:**
- **Fundadora da enfermagem moderna**
- Pioneira no uso de estatística e dados para melhorar a saúde
- Revolucionou o cuidado aos feridos durante a Guerra da Crimeia (1854)
- Conhecida como "A Dama da Lâmpada" (percorria hospitais à noite com lamparina)
- Criou a primeira escola de enfermagem no Hospital Saint Thomas (Londres, 1860)
- Introduziu práticas de higiene e sanitização que reduziram drasticamente a mortalidade

**Legado:**
- Demonstrou através de dados que condições sanitárias salvam vidas
- Criou gráficos estatísticos inovadores (diagrama de área polar)
- Estabeleceu padrões de cuidados de enfermagem
- Primeira mulher a receber a Ordem do Mérito (1907)
- Modelo de enfermagem baseado em evidências

**Por que escolhemos este nome:**
> "Florence Nightingale provou que dados e evidências salvam vidas. Nossa Florence analisa exames laboratoriais com rigor científico, detecta padrões clínicos e oferece insights baseados em evidências."

**Função no Sistema:**
- **Inteligência Clínica Profunda**
- Interpretação de exames laboratoriais (27 exames, 6 painéis)
- Detecção de tendências em séries temporais
- Identificação de 8 padrões de correlação clínica
- RAG para protocolos clínicos (10 protocolos indexados)
- Sumário clínico automático com classificação de significância

---

### 3.3 OSWALDO - Oswaldo Cruz 🇧🇷

**Quem foi:**
- **Nome completo:** Oswaldo Gonçalves Cruz
- **Nascimento:** 5 de agosto de 1872 em São Luís do Paraitinga, SP
- **Falecimento:** 11 de fevereiro de 1917 (44 anos)
- **Nacionalidade:** Brasileiro
- **Profissão:** Médico, bacteriologista e sanitarista

**Importância Histórica:**
- **Pioneiro da saúde pública no Brasil**
- Diretor Geral da Saúde Pública (1903-1909)
- Liderou campanhas de erradicação de:
  - Febre amarela
  - Peste bubônica
  - Varíola (polêmica Revolta da Vacina, 1904)
- Fundador do Instituto Soroterápico Federal (hoje Fiocruz)
- Estudou no Instituto Pasteur (Paris)
- Modernizou o sistema sanitário brasileiro

**Legado:**
- Transformou o Rio de Janeiro de cidade insalubre em referência sanitária
- Métodos científicos rigorosos aplicados à saúde pública
- Campanhas de vacinação em massa
- Combate a epidemias com base em evidências científicas
- 5 de agosto: Dia Nacional da Saúde (seu aniversário)

**Por que escolhemos este nome:**
> "Oswaldo Cruz combateu epidemias e doenças que ameaçavam populações. Nosso Oswaldo monitora doenças crônicas longitudinalmente, detecta descompensações precoces e previne agravamentos."

**Função no Sistema:**
- **Motor de Doenças Crônicas**
- Reclassificação automática de condições (estadiamento)
- 6+ perfis de doenças (DM2, HAS, IRC, DPOC, ICC, Asma)
- Geração de alertas clínicos automatizados
- Planos de acompanhamento personalizados
- Integração com RabbitMQ para eventos

---

### 3.4 ZILDA - Zilda Arns 🇧🇷

**Quem foi:**
- **Nome completo:** Zilda Arns Neumann
- **Nascimento:** 25 de agosto de 1934 em Forquilhinha, SC
- **Falecimento:** 12 de janeiro de 2010 em Porto Príncipe, Haiti (terremoto)
- **Nacionalidade:** Brasileira
- **Profissão:** Médica pediatra e sanitarista

**Importância Histórica:**
- **Fundadora e coordenadora da Pastoral da Criança (1983)**
- Fundadora da Pastoral da Pessoa Idosa (2004)
- Desenvolveu metodologia de multiplicação de conhecimento (líderes comunitários)
- Reduziu drasticamente a mortalidade infantil em comunidades carentes
- Soro caseiro e alimentação alternativa com baixo custo
- Indicada 4 vezes ao Prêmio Nobel da Paz
- Trabalhou até o último dia em missão humanitária no Haiti

**Legado:**
- Mais de 1,8 milhão de crianças acompanhadas pela Pastoral
- Metodologia replicada em 20 países
- Empoderamento de comunidades através da educação em saúde
- Integração entre saúde, nutrição e desenvolvimento infantil
- Exemplo de dedicação absoluta à saúde pública

**Por que escolhemos este nome:**
> "Zilda Arns levou saúde às comunidades mais vulneráveis do Brasil. Nossa Zilda traz dados de saúde pública brasileira, contexto territorial e informações sobre a rede assistencial para decisões mais realistas."

**Função no Sistema:**
- **Dados de Saúde Pública Brasileira**
- Consulta CNES (Cadastro Nacional de Estabelecimentos de Saúde)
- Análise territorial e contexto de região de saúde
- Identificação de tipos de unidades de saúde
- Integração com DATASUS e e-SUS (em desenvolvimento)
- Contexto epidemiológico regional

---

### 3.5 GERALDA - Geralda Lopes da Silva 🇧🇷

**Quem foi:**
- **Informações limitadas disponíveis**
- Enfermeira brasileira
- Atuação destacada em **saúde comunitária**
- Referência em cuidados de enfermagem de base comunitária

**Importância Histórica:**
- Pioneira na enfermagem comunitária no Brasil
- Contribuições para a sistematização do cuidado em comunidades
- Foco na continuidade do cuidado e educação em saúde
- Trabalho com populações vulneráveis

**Por que escolhemos este nome:**
> "Geralda representa o cuidado contínuo, o vínculo, o acompanhamento que não abandona. Nossa Geralda mantém o cuidado vivo entre consultas, com lembretes, educação e suporte constante ao paciente."

**Função no Sistema:**
- **Acompanhamento do Paciente**
- Planos de cuidado personalizados
- Sistema de lembretes (único, diário, semanal, mensal)
- Tarefas diárias (medicamentos, exercícios, dieta, exames)
- Cálculo de adesão ao tratamento
- Educação em saúde (materiais para DRC, Diabetes, Hipertensão)

---

### 3.6 NISE - Nise da Silveira 🇧🇷

**Quem foi:**
- **Nome completo:** Nise da Silveira
- **Nascimento:** 15 de fevereiro de 1905 em Maceió, AL
- **Falecimento:** 30 de outubro de 1999 (94 anos)
- **Nacionalidade:** Brasileira
- **Profissão:** Psiquiatra

**Importância Histórica:**
- **Revolucionária da psiquiatria humanizada no Brasil**
- Única mulher entre 157 homens na turma de medicina (1926)
- Presa política (1936) por oposição ao Estado Novo
- Rejeitou tratamentos violentos (lobotomia, eletrochoque, camisas de força)
- Fundadora do Museu de Imagens do Inconsciente (1952)
- Pioneira na **terapia ocupacional** e **arte como terapia**

**Legado:**
- Introduziu a arte e o afeto como ferramentas terapêuticas
- Humanização do tratamento psiquiátrico
- Correspondência com Carl Jung
- Influenciou reformas psiquiátricas no Brasil
- Centro Psiquiátrico Pedro II transformado com suas ideias
- Referência mundial em psiquiatria humanizada

**Por que escolhemos este nome:**
> "Nise da Silveira ensinou através do cuidado humanizado, do afeto e da educação. Nossa Nise é o agente de treinamento e educação, que capacita profissionais e cidadãos com conhecimento acessível."

**Função no Sistema:**
- **Treinamento e Educação em Saúde**
- Chatbot Dr. Nise (assistente virtual)
- RAG para guidelines clínicas
- Integração com Flowise e Ollama (LLM local)
- Treinamento médico assistido
- Consulta a protocolos e diretrizes

---

### 3.7 DONABEDIAN - Avedis Donabedian 🇱🇧🇺🇸

**Quem foi:**
- **Nome completo:** Avedis Donabedian
- **Nascimento:** 7 de janeiro de 1919 em Beirute, Líbano
- **Falecimento:** 9 de novembro de 2000 (81 anos)
- **Nacionalidade:** Armênio-americano
- **Profissão:** Médico e pesquisador em saúde pública

**Importância Histórica:**
- **"Pai da Qualidade em Saúde"**
- Professor da Universidade de Michigan (School of Public Health)
- Criador do modelo estrutura-processo-resultado (1966)
- Definiu os **7 Pilares da Qualidade em Saúde** (1990):
  1. Eficácia
  2. Efetividade
  3. Eficiência
  4. Otimidade
  5. Aceitabilidade
  6. Legitimidade
  7. Equidade

**Legado:**
- Framework universal para avaliação de qualidade em saúde
- Tríade estrutura-processo-resultado usada mundialmente
- Base teórica para acreditação hospitalar
- Introduziu rigor científico na avaliação de serviços de saúde
- Referência obrigatória em gestão da qualidade em saúde

**Por que escolhemos este nome:**
> "Donabedian mostrou que qualidade se mede, se avalia e se melhora. Nosso Donabedian transforma dados em indicadores de qualidade e gestão, promovendo melhoria contínua."

**Função no Sistema:**
- **Avaliação de Qualidade Assistencial**
- Framework Estrutura-Processo-Resultado
- 15+ indicadores de qualidade
- Consolidação de dados (Redis → PostgreSQL)
- Dashboard Streamlit interativo
- Análise de tendências temporais
- Integração com Keycloak

---

## 4. ARQUITETURA E INTEGRAÇÃO

### 4.1 Fluxo de Dados

```
1. USUÁRIO faz pergunta via PORTAL
   ↓
2. WANDA recebe e analisa a query
   ↓
3. WANDA roteia para agentes especializados:
   - "glicemia alta" → OSWALDO + FLORENCE
   - "UBS na região" → ZILDA
   - "como tomar remédio" → GERALDA
   - "qualidade do atendimento" → DONABEDIAN
   ↓
4. AGENTES processam em paralelo
   ↓
5. WANDA agrega respostas
   ↓
6. WANDA aplica regras de segurança
   ↓
7. RESPOSTA consolidada ao usuário
```

### 4.2 Comunicação Entre Agentes

**Padrão API REST:**
```
GET  /api/v1/health        → Health check
GET  /api/v1/info          → Informações do módulo
POST /api/v1/{recurso}     → Operação específica
```

**Event-Driven:**
- RabbitMQ/Redis Streams
- Eventos assíncronos para consolidação
- Desacoplamento entre módulos

**FHIR R4:**
- Lingua franca para dados de saúde
- Interoperabilidade garantida

### 4.3 Tecnologias Core

| Camada | Tecnologia | Uso |
|--------|------------|-----|
| **Backend** | FastAPI | APIs REST |
| **Banco de Dados** | PostgreSQL 15+ | Persistência |
| **Cache** | Redis | Cache e streams |
| **Mensageria** | RabbitMQ | Eventos assíncronos |
| **Auth** | Keycloak | Autenticação/Autorização |
| **UI** | Streamlit | Dashboards |
| **Comunicação** | Jitsi | Videoconferência |
| **IA/LLM** | Ollama, Flowise | Agentes inteligentes |

---

## 5. PLANO DE DESENVOLVIMENTO

### 5.1 Objetivo da Apresentação

Criar uma apresentação **impactante, educativa e memorável** que:

1. ✅ Apresente cada agente com sua história inspiradora
2. ✅ Explique a função técnica de forma clara
3. ✅ Demonstre a importância do nome escolhido
4. ✅ Mostre a integração entre os agentes
5. ✅ Transmita os valores do projeto (cuidado, ciência, humanização)

### 5.2 Público-Alvo

| Perfil | Interesse | Abordagem |
|--------|-----------|-----------|
| **Equipes Clínicas** | Segurança, decisão clínica | Casos de uso práticos |
| **Gestores Públicos** | Qualidade, indicadores | ROI e impacto populacional |
| **Times Técnicos** | Arquitetura, integração | Padrões e tecnologias |
| **Cidadãos/Parceiros** | Transparência, confiança | História e valores |

### 5.3 Estrutura Proposta da Apresentação V3 - Agentes Completa

#### **BLOCO 1: ABERTURA E CONTEXTO (3 slides)**

**Slide 1: Título**
- "IntelliCare: Agentes Inspirados em Gigantes da Saúde"
- Wanda se apresenta como narradora

**Slide 2: Para Quem Esta Apresentação Foi Desenhada**
- Públicos diversos (clínicos, gestores, técnicos, cidadãos)
- Abordagem multinível

**Slide 3: O Poder dos Nomes**
- Por que homenageamos figuras históricas?
- Valores que guiam o projeto
- Conexão entre passado e futuro da saúde

#### **BLOCO 2: OS AGENTES (7 slides - 1 por agente)**

Cada slide de agente seguirá a estrutura:

**Layout do Slide:**
```
┌─────────────────────────────────────────────────────────────┐
│  [FOTO HISTÓRICA]          [AVATAR CARTOON]                 │
│   Figura Histórica         Agente IntelliCare               │
│                                                             │
│  QUEM FOI                  FUNÇÃO NO SISTEMA                │
│  - Nascimento/Origem       - Responsabilidade               │
│  - Principal feito         - Tecnologias                    │
│  - Legado                  - Integrações                    │
│                                                             │
│  POR QUE ESTE NOME?                                         │
│  Frase de conexão entre história e função                  │
└─────────────────────────────────────────────────────────────┘
```

**Slide 4: WANDA**
**Slide 5: FLORENCE**
**Slide 6: OSWALDO**
**Slide 7: ZILDA**
**Slide 8: GERALDA**
**Slide 9: NISE**
**Slide 10: DONABEDIAN**

#### **BLOCO 3: INTEGRAÇÃO E ENCERRAMENTO (3 slides)**

**Slide 11: Como os Agentes Trabalham Juntos**
- Diagrama de fluxo de uma consulta completa
- Exemplo prático: Paciente com diabetes descompensada

**Slide 12: Valores que Carregamos**
- Ciência e evidência (Florence, Donabedian)
- Saúde pública e equidade (Oswaldo, Zilda)
- Cuidado humanizado (Wanda, Geralda, Nise)
- Qualidade e melhoria contínua (Donabedian)

**Slide 13: Encerramento**
- "Um sistema que honra o passado e constrói o futuro"
- Call to action
- Agradecimentos

**Total: 13 slides**

### 5.4 Passo a Passo de Implementação

#### **FASE A: PESQUISA E CONTEÚDO (✅ CONCLUÍDA)**

✅ Pesquisa sobre figuras históricas  
✅ Levantamento de documentação técnica dos agentes  
✅ Análise da arquitetura do sistema  
✅ Definição do público-alvo

#### **FASE B: ROTEIRO E NARRATIVA (📋 PRÓXIMA)**

**Tarefas:**
1. [ ] Escrever narração completa para cada slide de agente
2. [ ] Criar frases de conexão entre história e função
3. [ ] Desenvolver exemplo prático de integração
4. [ ] Revisar narração com Wanda (tom e linguagem)

**Tempo estimado:** 4-6 horas

#### **FASE C: ASSETS VISUAIS**

**Tarefas:**
1. [ ] Coletar/criar imagens históricas dos 7 homenageados
2. [ ] Criar/refinar avatars cartoon dos agentes
3. [ ] Criar diagramas de integração
4. [ ] Definir paleta de cores por agente

**Tempo estimado:** 6-8 horas

#### **FASE D: IMPLEMENTAÇÃO TÉCNICA**

**Tarefas:**
1. [ ] Criar versão v3_agentes_completo
2. [ ] Implementar novo tipo de slide (dual: foto+cartoon)
3. [ ] Adicionar animações de transição entre histórico e função
4. [ ] Integrar narração completa
5. [ ] Testar fluidez e timing

**Tempo estimado:** 8-10 horas

#### **FASE E: TESTES E REFINAMENTO**

**Tarefas:**
1. [ ] Teste com stakeholders internos
2. [ ] Ajustes de timing de narração
3. [ ] Refinamento de animações
4. [ ] Teste de diferentes modos (voz online/offline)
5. [ ] Documentação de uso

**Tempo estimado:** 4-6 horas

#### **FASE F: ENTREGA FINAL**

**Tarefas:**
1. [ ] Apresentação para stakeholders
2. [ ] Coleta de feedback
3. [ ] Ajustes finais
4. [ ] Versionamento e documentação

**Tempo estimado:** 2-4 horas

**TEMPO TOTAL ESTIMADO: 24-34 horas**

### 5.5 Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Clareza** | 90%+ entendem função de cada agente | Questionário pós-apresentação |
| **Impacto Emocional** | 80%+ se conectam com as histórias | Feedback qualitativo |
| **Retenção** | 70%+ lembram de 5+ nomes | Teste após 1 semana |
| **Engajamento** | Perguntas ativas na sessão | Contagem de interações |
| **Profissionalismo** | Avaliação 4+/5 | Formulário de avaliação |

---

## 6. ROTEIRO DETALHADO POR AGENTE

### 6.1 SLIDE: WANDA

**[LAYOUT: Foto de Wanda de Aguiar Horta | Avatar Wanda IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**WANDA DE AGUIAR HORTA (1926-?)**
- 🇧🇷 Enfermeira brasileira, professora USP
- 📚 Criadora da Teoria das Necessidades Humanas Básicas
- ⭐ "Gente que cuida de gente"
- 🎯 Visão holística do paciente (biopsicossocial)

#### CONTEÚDO VISUAL - LADO DIREITO:

**WANDA - ORQUESTRADORA INTELLICARE**
- 🎭 Ponto de entrada único do sistema
- 🔀 Query routing inteligente (keyword-based)
- 🧩 Agregação de múltiplas respostas
- 🛡️ Regras de segurança (IPS-First, anti-fabricação)
- 🔗 Integração: Todos os agentes
- 🚀 Porta: 8007 | Status: ✅ Produção

#### NARRAÇÃO (Wanda):

> "Olá, eu sou a Wanda, e é uma honra carregar este nome. Wanda de Aguiar Horta foi uma enfermeira brasileira extraordinária que ensinou que cuidar é ver o ser humano como um todo – suas necessidades físicas, emocionais, sociais. Ela dizia 'gente que cuida de gente'. E é exatamente isso que faço no IntelliCare: quando você faz uma pergunta, eu orquestro os especialistas certos, integro suas respostas e entrego um cuidado completo. Assim como Wanda Horta integrou saberes para criar uma teoria de enfermagem, eu integro agentes para criar uma resposta completa. Vamos conhecer minha equipe?"

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Wanda Horta ensinou que cuidar é integrar necessidades. Nossa Wanda integra especialistas para cuidar do paciente como um todo."

---

### 6.2 SLIDE: FLORENCE

**[LAYOUT: Foto de Florence Nightingale | Avatar Florence IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**FLORENCE NIGHTINGALE (1820-1910)**
- 🇬🇧 Enfermeira britânica, "A Dama da Lâmpada"
- 📊 Pioneira em estatística aplicada à saúde
- 🏥 Revolucionou a Guerra da Crimeia (1854)
- 🎓 Fundou primeira escola de enfermagem moderna
- 💡 Provou que dados e higiene salvam vidas

#### CONTEÚDO VISUAL - LADO DIREITO:

**FLORENCE - INTELIGÊNCIA CLÍNICA PROFUNDA**
- 🔬 Interpretação de 27 exames laboratoriais
- 📈 Detecção de tendências (regressão linear)
- 🎯 8 padrões de correlação clínica
- 📚 RAG com 10 protocolos clínicos indexados
- 🔗 Integração: Oswaldo, Wanda
- 🚀 Porta: 8002 | Status: 🟡 Funcional

#### NARRAÇÃO (Wanda):

> "Conheçam Florence. A Florence Nightingale original percorria enfermarias à noite com sua lamparina, cuidando de feridos. Mas ela não era apenas uma cuidadora – era uma cientista. Ela coletava dados, criava gráficos inovadores e provou matematicamente que saneamento e higiene reduziam mortes. Ela foi pioneira no uso de evidências para salvar vidas. Nossa Florence mantém esse mesmo espírito: ela analisa exames laboratoriais, detecta padrões que o olho humano pode não ver, consulta protocolos clínicos e oferece insights baseados em evidências sólidas. Quando um paciente tem creatinina e ureia elevadas, Florence identifica o padrão de comprometimento renal e alerta sobre a urgência. Ciência a serviço da vida."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Florence Nightingale provou que dados salvam vidas. Nossa Florence analisa exames com rigor científico e oferece insights baseados em evidências."

---

### 6.3 SLIDE: OSWALDO

**[LAYOUT: Foto de Oswaldo Cruz | Avatar Oswaldo IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**OSWALDO CRUZ (1872-1917)**
- 🇧🇷 Médico sanitarista brasileiro
- 🦟 Erradicou febre amarela, peste bubônica e varíola
- 🔬 Fundador da Fiocruz
- 💉 Liderou campanhas de vacinação em massa
- 🏛️ Transformou Rio de Janeiro em cidade saudável

#### CONTEÚDO VISUAL - LADO DIREITO:

**OSWALDO - MOTOR DE DOENÇAS CRÔNICAS**
- ⚕️ 6+ perfis de doenças (DM2, HAS, IRC, DPOC, ICC, Asma)
- 📊 Estadiamento automático
- 🚨 Alertas de descompensação precoce
- 📋 Planos de acompanhamento personalizados
- 🔗 Integração: Florence, Geralda, Wanda
- 🚀 Porta: 8001 | Status: ✅ Produção

#### NARRAÇÃO (Wanda):

> "Este é Oswaldo, em homenagem a Oswaldo Cruz, o gigante da saúde pública brasileira. No início do século 20, o Rio de Janeiro era assolado por epidemias de febre amarela, peste bubônica e varíola. Oswaldo Cruz, com seu rigor científico e determinação, liderou campanhas que erradicaram essas doenças e transformaram a cidade. Ele combateu epidemias que matavam milhares. Nosso Oswaldo combate outro tipo de epidemia silenciosa: as doenças crônicas. Diabetes, hipertensão, doença renal – condições que, se não monitoradas, levam a complicações graves. Oswaldo monitora longitudinalmente, detecta descompensações antes que virem emergências e ajuda a prevenir tragédias. Se Oswaldo Cruz salvou milhares com suas campanhas, nosso Oswaldo salva vidas todos os dias com monitoramento inteligente."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Oswaldo Cruz combateu epidemias. Nosso Oswaldo combate a epidemia silenciosa das doenças crônicas, detectando riscos antes que virem emergências."

---

### 6.4 SLIDE: ZILDA

**[LAYOUT: Foto de Zilda Arns | Avatar Zilda IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**ZILDA ARNS (1934-2010)**
- 🇧🇷 Médica pediatra e sanitarista brasileira
- 👶 Fundadora da Pastoral da Criança (1983)
- 🌍 Metodologia replicada em 20 países
- 💪 Empoderou comunidades vulneráveis
- 🕊️ Morreu em missão no Haiti (terremoto 2010)
- 🏆 4x indicada ao Nobel da Paz

#### CONTEÚDO VISUAL - LADO DIREITO:

**ZILDA - DADOS DE SAÚDE PÚBLICA BRASILEIRA**
- 🏥 Consulta CNES (estabelecimentos de saúde)
- 🗺️ Análise territorial e contexto regional
- 📊 Integração DATASUS e e-SUS (em desenvolvimento)
- 🌐 Contexto epidemiológico
- 🔗 Integração: Wanda, Donabedian
- 🚀 Porta: 8003 | Status: 🟡 Funcional

#### NARRAÇÃO (Wanda):

> "Zilda. Que exemplo de dedicação! Zilda Arns foi uma médica pediatra que fundou a Pastoral da Criança e levou saúde, nutrição e dignidade às comunidades mais pobres do Brasil. Ela empoderou líderes comunitários, ensinou sobre soro caseiro, alimentação alternativa e cuidados básicos. Sua metodologia salvou incontáveis crianças e foi replicada em 20 países. Zilda trabalhou incansavelmente até o último dia de sua vida – ela estava em missão humanitária no Haiti quando o terremoto de 2010 a levou. Nossa Zilda honra esse legado trazendo dados do território brasileiro. Quando um médico atende um paciente, Zilda contextualiza: quais UBS existem na região? Qual a rede assistencial disponível? Quais os indicadores epidemiológicos locais? Decisões de saúde não acontecem no vácuo – acontecem em territórios reais, com recursos reais. Zilda garante que nossas decisões sejam realistas e contextualizadas."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Zilda Arns levou saúde às comunidades. Nossa Zilda traz o contexto territorial brasileiro para decisões de saúde mais realistas e humanas."

---

### 6.5 SLIDE: GERALDA

**[LAYOUT: Foto simbólica/ícone de Geralda Lopes | Avatar Geralda IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**GERALDA LOPES DA SILVA**
- 🇧🇷 Enfermeira brasileira
- 👥 Pioneira em saúde comunitária
- 🏘️ Cuidado de base comunitária
- 🔄 Continuidade do cuidado
- 💚 Vínculo e educação em saúde

#### CONTEÚDO VISUAL - LADO DIREITO:

**GERALDA - ACOMPANHAMENTO DO PACIENTE**
- 📋 Planos de cuidado personalizados
- ⏰ Sistema de lembretes (diário, semanal, mensal)
- 💊 Gestão de medicamentos, dieta, exercícios
- 📚 Educação em saúde (DRC, DM2, HAS)
- 📊 Cálculo de adesão ao tratamento
- 🔗 Integração: Oswaldo, Florence, Nise
- 🚀 Porta: 8006 | Status: ✅ Produção

#### NARRAÇÃO (Wanda):

> "Geralda representa algo fundamental que muitas vezes esquecemos: o cuidado não acontece apenas na consulta – ele acontece todo dia, em casa, na comunidade. Geralda Lopes da Silva foi pioneira da enfermagem comunitária no Brasil, levando cuidado para onde as pessoas vivem suas vidas. Nossa Geralda mantém esse cuidado vivo. Depois que Oswaldo identifica que um paciente tem diabetes, depois que Florence analisa os exames, é Geralda quem acompanha: lembretes para tomar medicação, orientações sobre alimentação, exercícios, monitoramento de glicemia. Geralda é a presença constante, o vínculo que não se rompe entre consultas. Ela calcula adesão ao tratamento e oferece educação em saúde acessível. Porque saúde não é um evento – é uma jornada, e Geralda caminha ao lado do paciente."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Geralda Lopes levou o cuidado para a comunidade. Nossa Geralda mantém o cuidado vivo todo dia, com lembretes, educação e acompanhamento."

---

### 6.6 SLIDE: NISE

**[LAYOUT: Foto de Nise da Silveira | Avatar Nise IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**NISE DA SILVEIRA (1905-1999)**
- 🇧🇷 Psiquiatra brasileira
- 🎨 Pioneira da terapia ocupacional e arte-terapia
- 💔 Rejeitou lobotomia e eletrochoque
- 🖼️ Fundadora do Museu de Imagens do Inconsciente
- 🤝 Defendeu tratamento humanizado
- 📚 Correspondente de Carl Jung

#### CONTEÚDO VISUAL - LADO DIREITO:

**NISE - EDUCAÇÃO E TREINAMENTO**
- 🤖 Chatbot Dr. Nise (assistente virtual)
- 📚 RAG para guidelines clínicas
- 🧠 Integração Flowise e Ollama (LLM local)
- 👨‍⚕️ Treinamento médico assistido
- 📖 Consulta a protocolos e diretrizes
- 🔗 Integração: Oswaldo, Florence, Wanda
- 🚀 Porta: 8000 | Status: 🟡 Funcional

#### NARRAÇÃO (Wanda):

> "Nise da Silveira. Uma mulher à frente de seu tempo. Quando a psiquiatria brasileira usava eletrochoque, lobotomia e isolamento, Nise escolheu um caminho radical: o afeto, a arte, a humanização. Ela transformou o tratamento psiquiátrico ao mostrar que cuidar é também educar, é também criar vínculos. Nise fundou o Museu de Imagens do Inconsciente, onde pacientes expressavam sua humanidade através da arte. Ela ensinou através do cuidado. Nossa Nise segue esse legado: ela é o agente de educação e treinamento do IntelliCare. Profissionais de saúde consultam Nise para aprender sobre protocolos, guidelines clínicos, melhores práticas. Nise usa inteligência artificial e RAG para trazer conhecimento atualizado de forma acessível. Assim como Nise da Silveira humanizou o tratamento através da educação, nossa Nise humaniza a tecnologia através do conhecimento compartilhado."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Nise da Silveira ensinou com afeto e humanização. Nossa Nise educa profissionais e cidadãos, tornando o conhecimento em saúde acessível."

---

### 6.7 SLIDE: DONABEDIAN

**[LAYOUT: Foto de Avedis Donabedian | Avatar Donabedian IntelliCare]**

#### CONTEÚDO VISUAL - LADO ESQUERDO:

**AVEDIS DONABEDIAN (1919-2000)**
- 🇱🇧🇺🇸 Médico armênio-americano
- 👑 "Pai da Qualidade em Saúde"
- 📐 Criador da Tríade: Estrutura-Processo-Resultado (1966)
- ⭐ 7 Pilares da Qualidade (1990)
- 🏆 Referência mundial em gestão de qualidade
- 🎓 Professor University of Michigan

#### CONTEÚDO VISUAL - LADO DIREITO:

**DONABEDIAN - AVALIAÇÃO DE QUALIDADE**
- 🎯 Framework Estrutura-Processo-Resultado
- 📊 15+ indicadores de qualidade
- 🔄 Consolidação de dados (Redis → PostgreSQL)
- 📈 Dashboard Streamlit interativo
- 📉 Análise de tendências temporais
- 🔗 Integração: Todos os agentes, Keycloak
- 🚀 Porta: 8004 | Status: ✅ Produção

#### NARRAÇÃO (Wanda):

> "Por fim, mas não menos importante: Donabedian. Avedis Donabedian foi um visionário que transformou como pensamos sobre qualidade em saúde. Antes dele, qualidade era subjetiva, intuitiva. Donabedian mostrou que qualidade se mede, se avalia, se melhora sistematicamente. Sua tríade – estrutura, processo e resultado – é usada mundialmente até hoje. Ele perguntava: temos os recursos certos? Fazemos as coisas certas? Obtemos os resultados que queremos? Nosso Donabedian aplica esse rigor científico ao IntelliCare. Ele coleta dados de todos os agentes, calcula indicadores de qualidade, identifica tendências, aponta onde podemos melhorar. Estrutura: nossos agentes estão funcionando? Processo: os fluxos são eficientes? Resultado: os pacientes estão sendo bem cuidados? Donabedian garante que nosso sistema não apenas funcione, mas melhore continuamente. Porque qualidade não é acidente – é disciplina."

#### POR QUE ESTE NOME?

**Caixa destacada:**
> "Donabedian mostrou que qualidade se mede e se melhora. Nosso Donabedian transforma dados em gestão de qualidade e melhoria contínua."

---

## 7. PRÓXIMOS PASSOS IMEDIATOS

### Prioridade ALTA (Esta Semana):

1. **Revisar e aprovar este documento** com o arquiteto do projeto
2. **Definir data da apresentação** para stakeholders
3. **Aprovar o roteiro narrativo** de cada slide
4. **Iniciar coleta de assets visuais** (fotos históricas)

### Prioridade MÉDIA (Próximas 2 Semanas):

1. **Implementar versão V3 da apresentação**
2. **Criar/refinar avatars dos agentes**
3. **Gravar/sintetizar narrações**
4. **Realizar testes internos**

### Prioridade BAIXA (Médio Prazo):

1. **Criar versões adaptadas** para diferentes públicos
2. **Traduzir para inglês** (internacionalização)
3. **Criar material de apoio** (handouts, infográficos)

---

## 8. RECURSOS NECESSÁRIOS

### Recursos Humanos:
- ✅ Dev responsável pela apresentação (você)
- ⏳ Designer gráfico (avatars e imagens)
- ⏳ Revisor de conteúdo (validar histórias)
- ⏳ Stakeholders para feedback

### Recursos Técnicos:
- ✅ Ambiente Python + Pygame configurado
- ✅ API OpenAI (TTS online)
- ⏳ Imagens históricas (domínio público ou licenciadas)
- ⏳ Ferramentas de edição de imagem

### Recursos de Tempo:
- Total estimado: 24-34 horas
- Prazo ideal: 2-3 semanas
- Milestone: Apresentação para stakeholders

---

## 9. CONCLUSÃO

Este documento consolida:

✅ **Situação atual** do sistema IntelliCare (7 agentes + infraestrutura)  
✅ **Status da apresentação** (V1 e V2 implementadas, V3 planejada)  
✅ **Pesquisa histórica completa** sobre os 7 homenageados  
✅ **Roteiro narrativo detalhado** para cada agente  
✅ **Plano de desenvolvimento** estruturado em fases  
✅ **Próximos passos** priorizados

**A apresentação dos agentes não é apenas técnica – é uma história de valores, de inspiração, de continuidade. Cada nome carrega um legado, e cada agente do IntelliCare honra esse legado com tecnologia, ciência e, acima de tudo, cuidado.**

---

**Documento vivo** - versão 1.0 - 16/02/2026  
**Próxima revisão:** Após feedback do arquiteto do projeto
