# MCP INTELLICARE — DOCUMENTO TÉCNICO

# Sumário Executivo

O **MCP Intellicare (Model–Context–Protocol)** é o núcleo cognitivo e operacional da Plataforma Intellicare. Ele organiza e orquestra jornadas assistenciais coordenadas — inicialmente a Jornada de Internação do Serviço BemCuidar EC — com segurança, explicabilidade e governança institucional.

O MCP:

* interpreta eventos clínicos, operacionais e digitais;

* identifica o contexto assistencial relevante;

* aplica protocolos institucionais definidos na **Base de Conhecimento Clínico e Operacional (BCCO)**;

* aciona CPaaS, GC Cuidado, RSC-FHIR e Serviços de IA (Camada 4);

* garante que todas as ações sejam determinísticas, versionadas e auditáveis;

* integra hospital, APS, paciente e família em uma mesma narrativa assistencial.

Este documento descreve:

* a arquitetura completa da Plataforma Intellicare em **sete camadas**, indicando onde o MCP se posiciona;

* o funcionamento detalhado do Núcleo MCP (Model, Context, Protocol);

* a tipologia de contextos e critérios institucionais para criação de novos contextos;

* a Máquina de Estados MCP e a Matriz Evento → Contexto → Protocolo → Ações;

* a incorporação dos EventosJornadaEC como componente nativo do MCP;

* mecanismos de explicabilidade, auditoria, segurança, LGPD e governança;

* integração via RSC-FHIR como repositório clínico institucional;

* interação com CPaaS, IA Services, GC Cuidado e aplicações;

* roadmap técnico de implementação a partir da PoC C21–C22–C12.

O MCP posiciona o HDG e a Engenharia do Cuidado como referência nacional em coordenação digital da jornada, com IA supervisionada e segurança institucional.

# 1\. Introdução & Justificativa

Este documento é um desdobramento técnico da [**Arquitetura Conceitual da Plataforma Intellicare**](https://docs.google.com/document/d/1XlhRzUAhIwFiWinfmeOiBAiJARDVpFl4wYpJKLldCcg/edit?tab=t.0). Ele detalha exclusivamente o Núcleo MCP (Model–Context–Protocol) e não substitui o documento de Arquitetura, que permanece como fonte institucional para definições de camadas, papéis e responsabilidades macro.

O cuidado de pacientes com condições agudas e crônicas, em especial idosos e pessoas com múltiplas comorbidades, exige jornadas assistenciais complexas, que atravessam diferentes pontos da Rede de Atenção à Saúde (RAS). No contexto de hospitais SUS \- por exemplo, o Hospital  Dilson Godinho (HDG), e do Serviço BemCuidar EC, essa complexidade se manifesta de forma intensa na **transição do cuidado** entre hospital, família e Atenção Primária à Saúde (APS).

Tradicionalmente, essas jornadas são coordenadas com base em registros fragmentados, decisões locais de cada profissional e uma forte dependência da memória e da organização individual. Essa abordagem:

* aumenta o risco de falhas de comunicação;

* dificulta a integração hospital–APS;

* dificulta a identificação de momentos críticos (como previsão de alta, eventos de risco, sinais de descompensação após a alta);

* gera variabilidade na prática assistencial;

* torna os processos pouco explicáveis e difíceis de auditar.

Ao mesmo tempo, a Engenharia do Cuidado tem incentivado os hospitais SUS a adotarem uma visão mais ampla de **gestão do cuidado em rede**, articulando:

* o Serviço BemCuidar EC como núcleo de coordenação das jornadas assistenciais no contexto da atenção hospitalar e ambulatorial;

* a APS municipal como parceira estratégica;

* ferramentas digitais de comunicação (canais omnichannel seguros integrados ao WhatsApp para comunicar com pacientes e seu sistema de apoio);

* repositórios clínicos interoperáveis (RSC-FHIR);

* modelos de educação e aprendizagem baseados em mentoria e IA (AOM-IA).

Nesse contexto, a **Plataforma Intellicare** foi concebida para organizar, padronizar e potencializar a coordenação da jornada de cuidado. No centro dessa plataforma está o **Núcleo MCP Intellicare (Model–Context–Protocol)**.

## 1.1. Por que o MCP é necessário?

O MCP responde a desafios concretos:

* **Coerência da Jornada:** garante que eventos relacionados ao paciente (internação, mensagens de WhatsApp, notificações APS, tarefas internas) sejam interpretados sob uma mesma lógica de jornada.

* **Governança Institucional:** desloca a lógica de coordenação de dentro das aplicações (como CarePlanner) para um núcleo central com governança e  protocolos e contextos versionados.

* **Explicabilidade e Auditoria:** permite rastrear, explicar e auditar decisões clínicas e operacionais tomadas ao longo da jornada, inclusive aquelas mediadas por IA.

* **Uso Seguro de IA:** integra IA como assistente (triagem, síntese, apoio à comunicação), sem transferir a ela a responsabilidade pela decisão assistencial.

* **Integração Hospital–APS–Família:** articula canais digitais, rotinas assistenciais do hospital, fluxos da APS e o papel do cuidador/família em uma mesma narrativa.

## 1.2. Foco inicial: Jornada de Internação BemCuidar EC

Como estratégia de implementação progressiva, o MCP é inicialmente aplicado à **Jornada de Internação do Serviço BemCuidar EC**, com foco em:

* C1 — Paciente Internado (Contexto Raiz);

* C21 — Engajamento Digital Inicial Paciente/acompanhante;

* C22 — Engajamento Digital Inicial Coordenação APS;

* C12 — Conversa Inbound (mensagens iniciadas pelo paciente/acompanhante);

* outros contextos complementares de internação ( triagem, planejamento de alta, cuidados pós-alta, etc.), a serem incorporados conforme o roadmap.

Essa jornada é o “caso-base” da arquitetura MCP, servindo como laboratório institucional para posterior expansão a:

* jornadas de condições crônicas (ex.: DRC conservadora, IC, DM);

* jornadas oncológicas;

* jornadas paliativas;

* jornadas cirúrgicas.

## 1.3. Objetivos deste documento

Este documento técnico tem como objetivos:

* descrever a **arquitetura conceitual da Plataforma Intellicare** e o papel do MCP;

* detalhar o funcionamento do **Núcleo MCP (Model–Context–Protocol)**;

* definir a **tipologia e a máquina de estados** dos contextos MCP;

* apresentar a **matriz Evento → Contexto → Protocolo → Ações**;

* explicitar como o MCP se integra a **GC Cuidado, RSC-FHIR, CPaaS, IA Services e Aplicações**;

* formalizar a incorporação do **Processamento EventosJornadaEC como componente nativo do MCP** \- atualmente é um componente do CarePlanner;

* definir **mecanismos de explicabilidade, auditoria, segurança e governança**;

* apresentar um **roadmap técnico** para implementação progressiva, com ponto de partida na PoC C21–C22–C12.

# 2\. Arquitetura Conceitual Plataforma Intellicare

A Plataforma Intellicare organiza os componentes digitais, clínicos, operacionais, educativos e de governança em **sete camadas conceituais**, que se articulam para sustentar a operação do MCP e dos serviços de coordenação da jornada.

As sete camadas são:

1. **Camada 1 \- Infraestrutura**

2. **Camada 2 \- Núcleo MCP (Model–Context–Protocol)**

3. **Camada 3 \- Base de Conhecimento Clínico e Operacional**

4. **Camada 4 \- Serviços de Inteligência (AI Services)**

5. **Camada 5 \- Comunicação & Engajamento (CPaaS)**

6. **Camada 6 \- Segurança, LGPD e Governança (incluindo IAM)**

7. **Camada 7 \- Aplicações Operacionais, Analíticas, Educacionais e Assistentes Virtuais**

## 2.1. Camada 1 — Infraestrutura

A Camada de Infraestrutura da Plataforma Intellicare é definida integralmente no documento **Arquitetura Conceitual da Plataforma Intellicare**.  
 Ela abrange:

* infraestrutura de computação e execução (servidores, containers, orquestração, observabilidade);  
* serviços de armazenamento e banco de dados (PostgreSQL, storage, Lakehouse);  
* repositórios operacionais e clínicos (GC Cuidado e RSC-FHIR Server);  
* subcamadas de Interoperabilidade e Integração (SmartInterFHIR, SmartAdapters);  
* serviços de dados e processamento (ETL/ELT, Mirth, Airflow);  
* subcamada de dispositivos e sensores.

### Visão MCP (o que importa para o Núcleo MCP)

O MCP utiliza a Infraestrutura em três formas:

**1\. Para leitura do estado clínico e operacional**

* lê estado clínico via RSC-FHIR;  
* lê estado operacional via GC Cuidado (completo, consistente e versionado).

**2\. Para registro de evidências formais da jornada assistencial**

* grava Communications, AuditEvents, DocumentReferences, Provenances no RSC-FHIR.

**3\. Para ingestão de eventos provenientes dos sistemas legados**

* recebe atualizações estruturadas pela subcamada de Interoperabilidade (SmartInterFHIR / SmartAdapters).

### Padrão arquitetural

**Toda definição estrutural da Infraestrutura reside no documento de Arquitetura Conceitual.**

**O MCP apenas consome serviços dessa camada, sem redefinir nada no nível de infraestrutura**

## 2.3. Camada 2 — Núcleo MCP (Model–Context–Protocol)

A Camada 2 é o núcleo inteligente da plataforma.  O Núcleo MCP é o componente responsável por interpretar eventos, compreender o estado da jornada, selecionar o contexto aplicável e executar protocolos institucionais.

A arquitetura do MCP é independente da infraestrutura, da BCCO, do FHIR e das aplicações.

Ele atua como **máquina de estados institucional**, garantindo execução determinística, auditável e padronizada da jornada.

Funções principais da Camada 2

* interpretar qualquer evento recebido pela plataforma;

* construir o estado clínico+operacional (Model);

* identificar o contexto institucional correto (Context);

* executar protocolos institucionais (Protocol);

* acionar CPaaS, CarePlanner/GC Cuidado, RSC-FHIR e IA Services;

* garantir explicabilidade, segurança e governança da jornada.

### Padrão arquitetural

Toda a lógica da jornada institucional reside exclusivamente no MCP.  
 As aplicações **não duplicam** lógica de evento→contexto→protocolo.

## 2.4. Camada 3 — Base de Conhecimento Clínico e Operacional (BCCO)

A BCCO é a fonte institucional de conteúdo da Plataforma Intellicare.

Ela define **o que** deve ser feito (protocolos, pathways, templates, materiais educativos), enquanto o MCP define **quando e como** aplicar.

Toda lógica institucional é governada aqui; nada fica “embutido” no código do MCP ou nas aplicações.

### Funções principais

* armazenar e versionar protocolos assistenciais e operacionais;

* fornecer conteúdo semântico ao MCP e à IA;

* padronizar comunicação, orientação e fluxos;

* garantir coerência institucional;

* separar completamente conhecimento de código.

### Padrão arquitetural

A BCCO **não executa nada**:  
 não envia mensagens, não ativa contextos, não interpreta eventos, não registra FHIR.  
 Ela é consumida pela IA e pelo MCP como fonte de verdade institucional.

## 2.4. Camada 4 \- Serviços de Inteligência (AI Services)

Os Serviços de Inteligência da Plataforma Intellicare fornecem **capacidade assistiva**, nunca decisória.

Eles operam exclusivamente sob supervisão do MCP e utilizando conteúdo institucional da BCCO.

### Funções principais

* triagem de intenção em mensagens inbound;  
* sumarização clínica assistida;  
* adaptação de linguagem;  
* recomendação educacional;  
* suporte a profissionais (Wanda);  
* suporte a pacientes/família (Geralda).

### Padrão arquitetural

* IA **não** toma decisões;  
* IA **não** envia mensagens;  
* IA **não** altera estado da jornada;  
* IA **sempre** é supervisionada pelo MCP;  
* todos os outputs da IA são auditáveis.

### Papel da IA no MCP

O MCP integra e controla IA apenas como:

* **auxiliadora** (triagem preliminar),  
* **produtora de conteúdo** (resumos, adaptações),  
* **suporte educacional** (conteúdos),  
* **mediadora de explicabilidade**.

A IA nunca executa protocolos.

## 2.5. Camada 5 — Comunicação & Engajamento (CPaaS)

A camada CPaaS é o transportador omnichannel da plataforma.  
 Ela envia e recebe mensagens, mas **não** decide o que, quando ou por quê.

### Funções principais

* transportar mensagens definidas pelo MCP;

* receber mensagens inbound (eventos digitais);

* registrar status digital (delivered, read, failed);

* fornecer webhooks para o Motor de Eventos MCP.

### Padrão arquitetural

* CPaaS não interpreta intenção;

* CPaaS não escolhe canal;

* CPaaS não ativa contextos;

* CPaaS não envia nada sem ordem do MCP.

## 2.6. Camada 6 — Segurança, LGPD e Governança (incluindo IAM)

A camada de segurança garante que todas as interações MCP ↔ Sistemas ↔ Aplicações ocorram dentro dos parâmetros legais, éticos e de governança.

### Funções principais

* IAM institucional (Keycloak) como autoridade de identidade;

* autenticação e autorização padronizadas;

* RBAC/ABAC;

* políticas LGPD (minimização, pseudonimização, consentimento);

* logs e auditoria (IAM, MCP, CPaaS, FHIR);

* governança da BCCO e IA;

* supervisão institucional da jornada.

### Padrão arquitetural

Toda comunicação entre camadas é autenticada via IAM e auditável.  
 Nenhum componente tem acesso além do mínimo necessário (least privilege).

## 2.7. Camada 7 — Aplicações Operacionais, Analíticas, Educacionais e Assistentes Virtuais

As aplicações Intellicare são consumidoras, nunca reprodutoras, da lógica do MCP.

### Funções principais das aplicações

* CarePlanner: interface operacional da equipe;  
* Dashboards operacionais e analíticos;  
* Simuladores AOM-IA;  
* Assistentes virtuais (Wanda, Geralda);  
* Aplicações APS.

### Padrão arquitetural

Todas as aplicações:

* consomem o MCP;  
* leem RSC-FHIR e GC Cuidado via MCP;  
* nunca enviam mensagens diretamente;  
* nunca ativam contextos;  
* nunca aplicam protocolos;  
* nunca escrevem no FHIR diretamente.

# 3\. Núcleo MCP — Model / Context / Protocol

O **Núcleo MCP** é o componente central da Camada 3\.  
 Ele organiza a lógica da jornada assistencial em três módulos:

* **Model** — representa o estado clínico e operacional relevante para a jornada.

* **Context** — interpreta o significado dos eventos à luz desse estado.

* **Protocol** — executa as ações padronizadas, gerando evidências em sistemas externos.

Essa separação permite que a plataforma:

* trate eventos de maneira consistente;

* mantenha a lógica de jornada independente das aplicações;

* evolua contextos e protocolos sem reescrever o núcleo;

* garanta explicabilidade (cada decisão pode ser rastreada ao Model, Context e Protocol envolvidos).

## 3.1. Módulo Model — Estado Clínico e Operacional

O **Model** fornece ao MCP a visão consolidada do estado do paciente e da jornada, combinando:

* estado clínico (via RSC-FHIR: Encounter, Condition, Observation, Communication, CarePlan etc.);

* estado operacional (via GC Cuidado: tarefas, pendências, responsáveis, status);

* parâmetros institucionais (por exemplo, vínculos APS, canal preferido, risco, estratificação).

Responsabilidades do Model:

* construir uma “fotografia atual” da jornada de um paciente;

* fornecer à Máquina de Estados MCP as informações necessárias para decidir quais contextos podem ser ativados;

* registrar e atualizar internamente o estado lógico da jornada (por exemplo, “C1 ativo”, “C21 concluído”, “C22 pendente”).

O Model **não** se conecta diretamente às telas.  
 Ele conversa com:

* RSC-FHIR (via APIs);

* GC Cuidado (repositório operacional);

* Motor de Eventos (que o aciona para enriquecer eventos).

## 3.2. Módulo Context — Significado dos Eventos

O **Context** é responsável por responder à pergunta:

“Dado este evento e este estado de jornada, **qual é o contexto relevante**?”

Ele:

* identifica qual contexto MCP está ou deve ser ativado;

* verifica pré-condições (por exemplo, se C1 está ativo, se já houve apresentação do serviço, se há APS vinculada);

* determina se um evento dispara um novo contexto, atualiza um contexto existente ou produz apenas uma evidência.

Exemplos:

* Um evento `apresentacao_servico.concluida` em um paciente com C1 ativo → ativa o contexto C21.

* Uma mensagem inbound (`msg.inbound`) com canal válido e internação ativa → ativa C12 (Conversa Inbound).

* Um evento de `previsao_alta.registrada` → ativa C33 (Programação de Alta).

O Context não decide quais ações concretas serão executadas; ele **decide qual contexto está em jogo**.  
 A decisão sobre as ações cabe ao Protocol.

## 3.3. Módulo Protocol — Ação & Evidência

O **Protocol** é responsável por transformar o contexto em ações concretas, seguindo padrões institucionais definidos na BCCO

* quais mensagens enviar (via CPaaS);

* quais tarefas criar/atualizar (via CarePlanner \+ GC Cuidado);

* quais registros clínicos gerar (via RSC-FHIR);

* quando acionar IA para triagem, síntese ou apoio à comunicação;

* quando escalar para pessoa humana (priorização, tarefas urgentes).

Aqui é importante aplicar a correção de responsabilidades:

* **CarePlanner** é a aplicação onde o profissional visualiza a jornada e **executa as ações nas tarefas** (criar, atualizar, encerrar), gerando **TaskEvent** e **UpdateTask**.

* **GC Cuidado** é o **repositório operacional** que armazena essas tarefas e eventos; ele **não executa** as ações, apenas armazena o estado e o histórico.

* O **Protocol** MCP orquestra e determina que tais ações devem ocorrer, chamando as APIs apropriadas (por exemplo, “criar uma nova tarefa no GC Cuidado via serviço do CarePlanner”).

Responsabilidades do Protocol:

* transformar uma decisão contextual (ex.: “ativar C21”) em uma sequência de ações técnicas;

* garantir que essas ações sejam determinísticas, versionadas e auditáveis;

* registrar o resultado da execução (sucesso, falha, retry) em logs e no FHIR (AuditEvent, Provenance, Communication quando cabível);

* acionar a IA (quando necessário) de forma segura e controlada (por exemplo, para classificar uma mensagem inbound ou adaptar linguagem para paciente com baixa literacia).

O Protocol **não decide sozinho qual contexto ativar** — isso é papel do Context. Ele executa o que foi determinado pelo MCP com base nas regras e protocolos da BCCO.

# 4\. Tipologia Operacional dos Contextos MCP

Os **Contextos MCP** são as unidades semânticas de organização da jornada assistencial.  
 Eles representam **estados operacionais ou clínicos significativos**, nos quais protocolos institucionais podem ser aplicados com segurança, coerência e explicabilidade.

Cada contexto:

* tem gatilhos bem definidos;

* depende do estado da jornada (Model);

* representa um “momento institucional” da jornada;

* ativa protocolos que geram ações determinísticas;

* registra evidências em RSC-FHIR e GC Cuidado.

Os contextos são agrupados em **cinco tipos operacionais**, de acordo com sua natureza e função institucional.

## 4.1. Contextos Clínicos (Tipo C)

Representam **estados assistenciais diretamente derivados de eventos clínicos** (por exemplo, admissão hospitalar, alta, mudança de risco).

Características:

* gatilho: evento clínico FHIR (Encounter, Condition, Observation);

* impacto direto no cuidado;

* frequentemente servem como “contextos raiz”.

Exemplos:

* **C1 — Paciente Internado (Raiz da jornada de internação)**

* C41 — Alta Clínica

* C51 — Triagem de Sintomas / Risco

## 4.2. Contextos Digitais / Sistema–IA (Tipo D)

Representam interações mediadas por CPaaS, IA ou automações.

Características:

* gatilho: mensagens inbound, detecção de canal, eventos digitais;

* frequentemente envolvem IA de triagem;

* exigem explicabilidade e supervisão.

Exemplos:

* **C12 — Conversa Inbound**

* **C21 — Engajamento Digital Inicial Paciente/Acompanhante**

* **C22 — Engajamento Digital Inicial APS**

## 4.3. Contextos Operacionais (Tipo O)

Representam estados relacionados à coordenação do cuidado: tarefas, pendências, articulação APS, regulação, preparo de alta.

Características:

* gatilho: eventos do CarePlanner (TaskEvent, UpdateTask), EventosJornadaEC;

* interagem intensamente com GC Cuidado;

* estruturam a operação do serviço.

Exemplos:

* **C33 — Programação de Alta**

* C52 — Acompanhamento Pós-Alta

## 4.4. Contextos de Governança (Tipo G)

Representam situações onde o MCP precisa garantir coerência, segurança, conformidade ou retomada do fluxo institucional.

Características:

* gatilho: falhas operacionais, inconsistências, duplicidades, eventos fora de ordem;

* atuam como “protetores da jornada”;

* podem gerar eventos sintéticos.

Exemplos:

* C90 — Consistência da Jornada

* C91 — Idempotência e Recuperação

* C92 — Conflito de Estado

## 4.5. Contextos Interativos Humano–IA–Humano (Tipo H)

Representam momentos em que a IA e o humano interagem mediando decisões assistenciais com supervisão do MCP.

Características:

* gatilho: solicitações da equipe (via CarePlanner), mensagens inbound complexas, análises de risco;

* MCP garante supervisão e explicabilidade da IA;

* produzem evidências ricas (DocumentReference, summaries).

Exemplos:

* C81 — Sumarização Clínica Assistida

* C82 — Explicabilidade Assistida (Wanda)

* C83 — Assistência Educacional (Geralda)

# 5\. Critérios para Criação de Novos Contextos MCP

Um novo contexto MCP só deve ser criado quando claramente necessário: 

* Criar contextos demais reduz clareza;   
* criar de menos gera ambiguidade.

A seguir estão os **critérios formais**, validados pelo NGC e vitais para governança.

## 5.1. Critério 1 — A ação esperada depende do estado da jornada

Um novo contexto é necessário quando **o comportamento desejado muda dependendo de onde o paciente está na jornada**.

**Exemplo institucional:**  
Na Jornada de Internação, elaborar um plano educativo para um paciente **analfabeto** (ou com baixa literacia) exige adaptações específicas de linguagem e protocolos diferentes.  
 → Isso só deve ocorrer se o contexto “C21 — Engajamento Digital Inicial” já tiver capturado a preferência e características do canal.  
 → Logo, um contexto digital específico pode ser necessário, se o comportamento for diferente.

## 5.2. Critério 2 — O evento tem significado próprio, distinto de outros

Eventos distintos que representam “coisas diferentes” devem ativar contextos diferentes.

**Exemplo:**

* previsão de alta é diferente de alta clínica.  
   → Devem existir C33 e C41.

* mensagem inbound é diferente de notificação APS.  
   → Devem existir C12 e C22.

## 5.3. Critério 3 — O protocolo é diferente dos já existentes

Se o conjunto de ações a executar é radicalmente diferente, o contexto novo é justificado.

**Exemplo:**  
 Programação de alta (C33) exige:

* checagem APS,

* educação,

* pendências,

* orientações pré-alta,

enquanto “orientação familiar” (C23) exige outro conjunto de ações.

## 5.4. Critério 4 — Há riscos assistenciais específicos

Se o risco de não tratar o evento de forma específica é alto, o MCP precisa de um contexto próprio.

**Exemplo:**  
 “dor moderada na alta” pode reabrir C51 triagem de sintomas, enquanto “dúvida sobre curativo” abre C23.  
 → Não podem ser tratados no mesmo contexto.

## 5.5. Critério 5 — Outro contexto não cobre adequadamente o caso

Caso não exista contexto que:

* garanta segurança,

* cubra pré-condições,

* acione protocolos apropriados,

* gere explicabilidade,

então cria-se um novo contexto.

## 5.6. Critério 6 — É necessário padronizar comportamento institucional

Se um processo precisa ser padronizado hospital–APS–família, o contexto ajuda a “trancar” essa padronização e garantir coerência.

**Exemplo:**  
Engajamento APS na internação (C22) padroniza notificações intersetoriais.

## 5.7. Critério 7 — Relevância para auditoria e explicabilidade

Se uma atividade futura precisa ser auditável e previsível, deve ser um contexto.

**Exemplo:**  
Evento “quebra de vínculo APS” exige contexto operacional C72.

# 6\. Máquina de Estados MCP

*(Versão revisada, robusta e alinhada ao Motor de Eventos)*

A **Máquina de Estados MCP** define como o núcleo interpreta a jornada a partir de:

* eventos recebidos,

* estado atual (Model),

* regras da BCCO,

* e contexto ativo.

Ela garante que:

* cada evento é interpretado de acordo com o estado da jornada;

* ações só ocorrem se o contexto for apropriado;

* o MCP seja determinístico, auditável e previsível.

## 6.1. Princípio — MCP é uma Máquina de Estados Semântica

O MCP NÃO é uma máquina de estados simples baseada apenas em transições lógico-matemáticas.

Ele é uma **máquina semântica**, baseada em:

* significados clínicos,

* significados operacionais,

* regras assistenciais,

* contexto institucional.

Cada estado representa **contextos ativos**, não apenas “flags”.

## 6.2. Elementos da Máquina de Estados

A Máquina de Estados MCP possui quatro componentes fundamentais:

**1\) Estado**

O conjunto de contextos ativos no momento (C1 ativo, C21 pendente, C22 concluído…).

**2\) Evento**

Algo que ocorre e é interpretado (entrada do Motor de Eventos):

* clínico (FHIR)

* digital (CPaaS)

* operacional (CarePlanner)

* APS

* sintético

**3\) Transição**

O que o MCP faz quando um evento ocorre em determinado estado:

```
(evento, estado) → novo contexto | atualização | ação | nada
```

**4\) Ações**

Executadas pelo módulo Protocol, nunca pelo Motor de Eventos.

## 6.3. Estados MCP (macrovisão)

A jornada BemCuidar pode ser representada em macroestados:

1. **E0 — Sem jornada ativa**

2. **E1 — Jornada de Internação ativa (C1)**

3. **E2 — Engajamento ativo (C21/C22)**

4. **E3 — Cuidados durante internação (vários contextos)**

5. **E4 — Programação alta (C33)**

6. **E5 — Alta clínica (C41)**

7. **E6 — Pós-alta (C52/C12 recorrente)**

8. **E7 — Encerramento (C99)**

## 6.4. Exemplo completo de transições (C21, C22 e C12)

**Transição 1 — Evento: apresentação\_serviço.concluída**

**Estado:** C1 ativo  
 **Ação:** ativar C21  
 **Protocolo:** enviar boas-vindas  
 **Evidência:** Communication(FHIR)

**Transição 2 — Evento: APS vinculada**

**Estado:** C1 ativo  
**Ação:** ativar C22  
**Protocolo:** notificar APS  
**Evidência:** Communication(FHIR)

**Transição 3 — Evento: msg.inbound**

**Estado:** qualquer estado com canal ativo  
**Ação:** ativar C12  
**Protocolo:** triagem IA \+ ação  
**Evidências:** Communication \+ TaskEvent

## 6.5. Governança da Máquina de Estados

A Máquina de Estados MCP é governada pelo:

* Regras de negócio estabelecidas pela Coordenação do Serviço BemCuidar EC;

* TI/Arquitetura;

* Privacidade e Segurança.

Alterações exigem:

1. Revisão de protocolos;

2. Atualização da BCCO;

3. Atualização da Matriz Evento→Contexto;

4. Versionamento;

5. Publicação institucional;

6. Comunicação e treinamento das equipes.

## 6.6. Benefícios da Máquina de Estados MCP

* garante consistência institucional;

* evita decisões divergentes;

* permite previsão e explicabilidade;

* reduz risco assistencial;

* integra hospital–APS–paciente;

* cria base para automação segura;

* viabiliza expansão para múltiplas jornadas.

# 7\. Matriz MCP: Evento → Contexto → Protocolo → Ações

A Matriz MCP é o **instrumento institucional central** para garantir que:

* eventos sejam interpretados corretamente

* contextos sejam ativados de forma determinística

* protocolos sejam aplicados conforme regras institucionais

* ações sejam rastreáveis, versionadas e auditáveis

Ela conecta, de forma explícita:

```
Evento → Estado (Model) → Contexto → Protocolo → Ações → Evidências
```

A Matriz não substitui a Máquina de Estados, mas a **complementa** como instrumento administrativo, regulatório e operacional, facilitando:

* governança clínica (Coordenação clínica do Serviço BemCuidar EC)

* padronização interequipes

* auditorias

* validação da IA

* testes e homologações

* implantação e expansão para novas jornadas

## 7.1. Estrutura da Matriz MCP

Cada linha da matriz possui:

| Campo | Descrição |
| ----- | ----- |
| **Evento MCP** | Evento bruto recebido pelo Motor de Eventos |
| **Estado Relevante (Model)** | Estado mínimo necessário para interpretar o evento |
| **Contexto Ativado** | O contexto MCP que deve ser ativado |
| **Protocolo Aplicado** | O protocolo institucional correspondente |
| **Ações Determinísticas** | Os comandos que o Protocol executa |
| **Evidências Registradas** | FHIR / GC Cuidado / Logs MCP |

## 7.2. Exemplos Institucionais (Jornada BemCuidar EC)

**Linha 1 — Apresentação do Serviço Concluída**

| Item | Valor |
| ----- | ----- |
| **Evento** | `evt.apresentacao_servico.concluida` |
| **Estado (Model)** | C1 ativo (internação em curso) |
| **Contexto Ativado** | **C21 — Engajamento Digital Inicial** |
| **Protocolo** | boas-vindas, consentimento, coleta de preferências |
| **Ações** | envio CPaaS; registro consentimento; atualização estado |
| **Evidências** | Communication(FHIR); AuditEvent |

**Linha 2 — Apresentação do Serviço Concluída**

| Item | Valor |
| ----- | ----- |
| **Evento** | `evt.apresentacao_servico.concluida com TCLE = S` |
| **Estado (Model)** | C1 ativo (internação em curso) |
| **Contexto Ativado** | **C22 — Engajamento Digital Inicial APS** |
| **Protocolo** | notificação Coordenação APS; registro institucional |
| **Ações** | envio CPaaS para APS; atualização tarefa |
| **Evidências** | Communication(FHIR); AuditEvent |

**Linha 3 — Mensagem Inbound**

| Item | Valor |
| ----- | ----- |
| **Evento** | `evt.msg.inbound` |
| **Estado (Model)** | canal ativo, internação ativa |
| **Contexto Ativado** | **C12 — Conversa Inbound** |
| **Protocolo** | triagem IA; acolhimento; orientação; tarefa |
| **Ações** | CPaaS resposta; criação de TaskEvent via CarePlanner |
| **Evidências** | Communication; TaskEvent |

## 7.3. Governança da Matriz MCP

A Matriz MCP é validada e versionada por:

* Nota Técnica Configuração Serviço BemCuidar EC

* TI / Arquitetura

* Privacidade / Segurança

Alterações exigem:

1. atualização da BCCO

2. atualização da Máquina de Estados

3. versionamento de protocolos

4. revisão e homologação

5. treinamento institucional

# 8\. Motor de Eventos MCP

O Motor de Eventos é a **porta de entrada** do MCP.  
Ele recebe eventos de múltiplas origens, normaliza-os, atribui significado, ordena, enriquece com o estado atual e envia para o módulo **Context**, que decidirá qual contexto MCP deve ser ativado.

Ele garante:

* idempotência

* ordenação temporal

* validação de estrutura

* associação correta a pacientes e jornadas

* integridade semântica

* registro de logs

* segurança e autenticação

## 8.1. Origem dos Eventos (oficiais)

**1\. RSC-FHIR (Clínicos)**

* Encounter.admit

* Encounter.discharge

* Condition

* Observation

**2\. CPaaS (Digitais)**

* mensagens inbound

* confirmação de recebimento email

* falhas de entrega

* status read/delivered

**3\. CarePlanner (via GC Cuidado)**

* TaskEvent (criação de tarefa)

* UpdateTask (atualização de tarefa)

* Conclusão de eventos de jornada (ex.: apresentação do serviço)

**4\. IA Assistiva (eventos sintéticos)**

* sugestões de triagem

* sumarizações

**5\. EventosJornadaEC (reposicionados no MCP)**

Agora tratados como eventos nativos do MCP.

## 8.2. Pipeline do Motor de Eventos

O pipeline possui **7 etapas**, cada uma obrigatória:

**(1) Recepção**

* recebe evento bruto

* valida identidade/autorização via IAM

**(2) Normalização**

* padroniza estrutura

* converte payload para o padrão MCP Event Schema

**(3) Idempotência**

* garante que eventos duplicados não causem ações duplicadas

* gera chave única:  
   `hash(evento + timestamp + origem + paciente_id)`

**(4) Enriquecimento (Model)**

* estado clínico via FHIR

* estado operacional via GC Cuidado

* parâmetros da jornada

* Paciente engajado

* APS vinculada

* canal, preferências etc.

**(5) Interpretação (Context)**

* decide qual contexto deve ser ativado

* atualiza estado semântico

**(6) Execução (Protocol)**

* envio CPaaS

* escrita em FHIR

* comando para CarePlanner criar/atualizar tarefas

* IA supervisionada

* callbacks

**(7) Geração de Evidências**

* Communication(FHIR)

* AuditEvent(FHIR)

* Provenance(FHIR)

* logs MCP

* TaskEvent/UpdateTask (via CarePlanner)

## 8.3. Propriedades do Motor

* determinístico

* auditável

* versionado

* seguro

* tolerante a falhas

* desacoplado das aplicações

* orientado a contexto

# 9\. Responsabilidades Cruzadas (MCP × IA × GC Cuidado × RSC-FHIR × CPaaS)

Esta seção define claramente **quem faz o quê**, evitando inconsistências e garantindo governança.

## 9.1. Responsabilidades do MCP

✔ interpretar eventos  
 ✔ determinar contexto (Context)  
 ✔ determinar ação (Protocol)  
 ✔ acionar CPaaS  
 ✔ acionar CarePlanner (para criar/atualizar tarefas)  
 ✔ registrar evidências no FHIR  
 ✔ garantir idempotência  
 ✔ garantir determinismo  
 ✔ controlar interação com IA  
 ✔ supervisionar protocolos  
 ✔ manter Máquina de Estados  
 ✔ manter lógica de jornada

❌ não armazena dados assistenciais  
 ❌ não cria tarefas diretamente  
 ❌ não toma decisões clínicas automatizadas sem protocolo  
 ❌ não substitui aplicações

## 9.2. Responsabilidades do GC Cuidado (Repositório Operacional)

✔ armazenar tarefas  
 ✔ armazenar TaskEvent/UpdateTask  
 ✔ fornecer estado operacional ao Model  
 ✔ manter histórico de decisões operacionais humanas

❌ não cria tarefas  
 ❌ não atualiza tarefas  
 ❌ não encerra tarefas  
 ❌ não interpreta contexto  
 ❌ não executa protocolos  
 ❌ não envia mensagens  
 ❌ não decide nada  
 ❌ não registra FHIR

## 9.3. Responsabilidades do CarePlanner (Aplicação Operacional)

✔ criar tarefas  
 ✔ atualizar tarefas  
 ✔ encerrar tarefas  
 ✔ registrar TaskEvent/UpdateTask  
 ✔ informar conclusão de eventos da jornada (ex.: apresentação)  
 ✔ interface da equipe para visualizar jornada  
 ✔ receber sugestões MCP/IA  
 ✔ enviar eventos ao MCP

❌ não ativa contextos  
 ❌ não aplica protocolos  
 ❌ não registra evidências FHIR  
 ❌ não envia mensagens CPaaS diretamente

## 9.4. Responsabilidades do RSC-FHIR (Repositório Clínico)

✔ armazenar evidências clínicas  
 ✔ manter timeline institucional  
 ✔ fornecer estado clínico ao Model  
 ✔ registrar Communications, AuditEvent, Provenance, Encounter, Condition  
 ✔ garantir integridade e interoperabilidade

❌ não decide protocolos  
 ❌ não interpreta jornada  
 ❌ não envia mensagens

## 9.5. Responsabilidades do CPaaS

✔ enviar mensagens definidas pelo MCP  
 ✔ receber mensagens inbound  
 ✔ registrar status (entregue, lida, falha)  
 ✔ fornecer webhook para eventos digitais

❌ não determina conteúdo da mensagem  
 ❌ não escolhe quando enviar  
 ❌ não ativa contextos  
 ❌ não aplica protocolos

## 9.6. Responsabilidades da IA Assistiva

✔ interpretar intenção (triagem)  
 ✔ adaptar linguagem  
 ✔ auxiliar síntese  
 ✔ gerar respostas preliminares  
 ✔ apoiar educação  
 ✔ apoiar análise de risco

Sempre sob supervisão do MCP.

❌ não decide contexto  
 ❌ não envia mensagens diretamente  
 ❌ não registra FHIR  
 ❌ não altera estado da jornada

# 10\. Base de Conhecimento Clínico e Operacional (BCCO) Intellicare

A **Base de Conhecimento Clínico e Operacional (BCCO)** é a camada conceitual e institucional que guarda **o conhecimento formal da organização**, utilizado pelo MCP, pelas aplicações, pela IA e pela APS.

Ela é o *cérebro institucional*, enquanto o MCP é o *órgão executor da lógica*.

## 10.1. Papel Institucional da BCCO

A BCCO contém:

* **protocolos assistenciais** (clínicos e operacionais);

* **templates de comunicação** para CPaaS;

* **conteúdos educativos** para pacientes e familiares;

* **modelos de síntese e sumarização**;

* **planos de cuidado padrão**;

* **glossários e terminologias institucionais**;

* **regras de jornada** e condições de transição;

* **regras operacionais APS**;

* **normas internas e diretrizes do NGC**;

* **lógica institucional não computável diretamente** (metadados, explicações, fluxos alternativos);

* **versões históricas (governança)**.

A BCCO é **curada**, **auditada**, **versionada**, **governada institucionalmente**, e separada completamente de:

* código,

* aplicações (CarePlanner),

* repositórios (GC Cuidado / FHIR),

* serviços de IA.

## 10.2. Os 4 tipos de conhecimento da BCCO

**1\. Conhecimento Clínico**

* protocolos de avaliação, risco, orientação;

* listas de verificação (pré-alta, alta, pós-alta);

* critérios clínicos de atenção;

* indicadores de deterioração.

**2\. Conhecimento Operacional**

* fluxo de tarefas;

* responsabilidades da equipe;

* transições hospital–APS;

* comunicação institucional padronizada.

**3\. Conhecimento Comunicacional**

* templates CPaaS;

* padrões de linguagem;

* níveis de literacia;

* mensagens sensíveis (más notícias, riscos, sintomas).

**4\. Conhecimento Educacional**

* materiais BemCuidar EC (educação familiar);

* vídeos, PDFs, ilustrações;

* guias de alta e pós-alta;

* protocolos amboss-like assistidos por IA.

## 10.3. Como a BCCO interage com o MCP

A BCCO fornece conteúdo padronizado; o MCP aplica conforme estado e contexto da jornada.

Exemplo:

* A BCCO tem o template:  
   “Olá, {nome}. Sou parte da equipe do BemCuidar EC.”

* O MCP decide **no C21** que precisa enviar esse template porque o evento é “apresentação concluída”.

* O CPaaS apenas **transporta**.

## 10.4. Versionamento e Governança da BCCO

A BCCO segue governança formal:

1. Proposta de novo conteúdo

2. Revisão clínica/técnica

3. Coordenação Serviço BemCuidar EC valida

4. Publicação e versionamento

5. Documentação

6. Ajuste da máquina de estados e da matriz MCP

7. Treinamento (AOM-IA / Wanda)

## 10.5. Evidência: a BCCO garante padronização e consistência institucional

Sem BCCO:

* cada profissional usa textos próprios;

* IA improvisa respostas;

* protocolos mudam sem controle;

* inconsistências surgem;

* impossível auditar.

Com BCCO:

* a jornada é padronizada;

* IA é supervisionada;

* MCP é previsível;

* pacientes recebem mensagens consistentes;

* APS recebe informações claras;

* rastreabilidade fica garantida.

# 11\. Serviços de Inteligência (IA Services)

Os **Serviços de Inteligência** da Plataforma Intellicare não substituem humanos, não tomam decisões de cuidado e não atuam diretamente nos sistemas.  
 Eles são **assistentes institucionais supervisionados**.

Eles operam **sempre** sob controle do MCP e **sempre** usando conteúdo institucional da BCCO.

## 11.1. Tipos de Serviços de IA da Plataforma

**1\. IA de Triagem de Intenção (Conversas Digitais)**

* identifica intenção da mensagem inbound;

* classifica em categorias (dúvida, sintoma, vínculo APS, risco, educação, etc.);

* fornece sugestão ao MCP;

* não toma decisão sozinho.

**Atuação típica:**  
 C12 — Conversa Inbound.

**2\. IA de Adaptação de Linguagem**

* reescreve mensagens para níveis diversos de literacia;

* cria versões simplificadas, respeitosas e seguras;

* usa templates institucionais da BCCO.

**3\. IA de Síntese e Sumarização Clínica**

* resume prontuário para profissionais;

* cria sínteses legíveis;

* gera relatórios de transição de cuidado;

* sempre registra no FHIR (DocumentReference) via MCP.

**4\. IA de Recomendação Educacional**

* sugere conteúdos educativos baseados em contexto;

* ex.: C23 (educação familiar), C52 (pós-alta).

**5\. IA para Profissionais (Wanda)**

* explica decisões do MCP;

* auxilia treinamento;

* detalha a jornada;

* fornece informações e materiais.

**6\. IA para Paciente/Família (Geralda)**

* amplia a comunicação humana;

* fornece orientações educativas;

* esclarece dúvidas básicas;

* sempre supervisionada pelo MCP.

## 11.2. Regras Institucionais para a IA

**A IA NUNCA:**

* ativa contextos;

* envia mensagens diretamente ao paciente;

* altera estado da jornada;

* cria ou atualiza tarefas;

* realiza ações sem MCP.

**A IA SEMPRE:**

* opera em segundo plano;

* produz sugestões para revisão pelo MCP;

* usa exclusivamente conteúdo institucional;

* passa por logs de auditoria;

* tem versão rastreável.

## 11.3. Governança da IA

* Coordenação Serviço BemCuidar EC \+ TI \+ Privacidade supervisionam

* Todos os outputs da IA são registrados

* Modelos e prompts são versionados

* Mudança de comportamento exige revalidação institucional

# 12\. CPaaS — Comunicação e Engajamento

A Camada 5 da arquitetura integra os **canais de comunicação omnichannel** utilizados pelo BemCuidar EC:

* WhatsApp Business API

* SMS

* E-mail

* Chat Web

* Notificações push

O CPaaS é um **transportador** confiável, com logs, status e callbacks.  
 Ele **não interpreta** conteúdo, **não decide** quando enviar mensagens e **não se comunica diretamente com pacientes ou APS** sem instrução do MCP.

## 12.1. Funções do CPaaS

✔ receber mensagens inbound (webhook)  
 ✔ entregar ao Motor de Eventos MCP  
 ✔ enviar mensagens definidas pelo MCP  
 ✔ registrar status: entregue, lido, falha  
 ✔ fornecer IDs de rastreamento  
 ✔ realizar fallback (SMS → WhatsApp, etc.) — quando configurado

## 12.2. O CPaaS NÃO faz

❌ interpretar intenção  
 ❌ decidir conteúdo  
 ❌ decidir momento  
 ❌ aplicar protocolo  
 ❌ identificar paciente  
 ❌ integrar com FHIR  
 ❌ criar tarefas  
 ❌ ativar contextos

## 12.3. Como o MCP usa o CPaaS

O MCP envia ao CPaaS:

* destinatário (paciente, APS, cuidador)

* template institucional da BCCO

* parâmetros contextuais (nome, horário, unidade etc.)

* instruções de canal

Após o envio, o CPaaS devolve:

* status

* confirmação

* eventuais falhas

Esses eventos retornam ao MCP como **eventos digitais** (`evt.msg.delivered`, `evt.msg.failed`).

## 12.4. Registros e Evidências

Toda comunicação enviada ou recebida via CPaaS é registrada como:

* **Communication(FHIR)**

* **AuditEvent(FHIR)**

* logs do CPaaS

* logs do MCP

Isso viabiliza:

* reconstituição da jornada

* auditorias clínicas

* transparência institucional

* segurança jurídico-regulatória

## 12.5. Por que CPaaS é separado de IA e de Aplicações

Separação fundamental para segurança:

* IA sugere → MCP decide → CPaaS envia

* CarePlanner não envia mensagens diretamente

* CPaaS não interage com IA

* CPaaS não tem lógica de cuidado

Essa separação garante:

* conformidade LGPD

* segurança institucional

* rastreabilidade ponta a ponta

* eliminação de riscos de respostas inadequadas ou tardias

# 13\. Segurança, LGPD e Governança

A segurança informacional e a conformidade com a LGPD são pilares fundamentais da Plataforma Intellicare. A arquitetura foi desenhada para garantir que todas as camadas — do MCP às aplicações, do CPaaS ao RSC-FHIR — operem de forma segura, explicável e auditável.

## 13.1. Princípios de Segurança Institucional

A camada de Segurança/LGPD se baseia nos seguintes princípios:

1. **Minimização de dados**

   * cada componente só acessa o necessário para sua função.

2. **Separação de funções**

   * MCP não envia mensagens diretamente;

   * IA não toma decisões;

   * CPaaS não interpreta conteúdo;

   * aplicações não definem lógica de jornada.

3. **Autenticação e Autorização (IAM institucional)**

   * Keycloak ou equivalente como autoridade central de identidade;

   * autenticação MFA quando aplicável;

   * autorização baseada em papéis (RBAC) e atributos (ABAC);

   * acesso contextual (perfil × unidade × função × situação do paciente).

4. **Auditoria completa**

   * todas as ações são registradas em AuditEvent/Provenance FHIR;

   * rastreabilidade ponta a ponta (MCP → FHIR → CPaaS → GC Cuidado).

5. **Supervisão humana**

   * IA nunca atua sem MCP;

   * MCP nunca toma decisões clínicas sem protocolo.

6. **Governança de conteúdo**

   * BCCO versionada e auditada;

   * protocolos só entram após aprovação do NGC.

## 13.2. IAM — Mecanismo Institucional de Identidade e Acesso

O IAM (ex.: Keycloak) opera integralmente na **Camada 6**, garantindo:

* autenticação única para todas as aplicações Intellicare;

* tokens de acesso com escopo limitado;

* controle de acesso granular:

  * ex.: enfermeiro só acessa pacientes de sua ala;

* autorização baseada em contexto:

  * unidade, turno, papel, tipo de dado;

* registro de sessões, tentativas e falhas.

**Integração com MCP**

* cada evento recebido pelo MCP é validado via token IAM;

* permissões determinam quais ações o usuário ou sistema pode acionar;

* acesso ao FHIR e GC Cuidado é intermediado pelo IAM.

## 13.3. LGPD — Implementação no MCP e na Plataforma Intellicare

**Bases legais aplicáveis**

* prestação de serviços de saúde;

* tutela da saúde;

* consentimento (quando aplicável);

* interesse legítimo institucional;

* regulamentos do SUS.

**Técnicas adotadas**

* **pseudonimização** para logs MCP e testes;

* **anonimização** para analytics e treinamentos;

* **masking** em campos sensíveis (telefone, endereço);

* **retenção controlada**;

* **baixa granularidade** no acesso (least privilege).

**Direitos do titular**

* transparência (Geralda pode explicar ao paciente por que recebeu mensagens);

* acesso aos registros (via FHIR);

* correção de informações;

* revogação de consentimento para canais digitais.

## 13.4. Governança Clínica e Operacional

A governança é estruturada por:

**Coordenação Serviço BemCuidar EC**

* curadoria de protocolos;

* definição de novos contextos MCP;

* validação da BCCO;

* supervisão da jornada.

**Comitê Clínico**

* valida conteúdo clínico;

* supervisiona risco assistencial.

**TI / Arquitetura**

* integra sistemas;

* implementa segurança;

* garante estabilidade.

**Comitê de Privacidade**

* supervisiona LGPD;

* aprova modelos de anonimização.

**APS**

* valida fluxos intersetoriais.

## 13.5. Auditoria MCP (Multicamadas)

A auditoria ocorre simultaneamente em:

* **MCP**: logs estruturados (evento, contexto, protocolo, ação, resultado)

* **RSC-FHIR**: AuditEvent, Provenance, Communication

* **GC Cuidado**: TaskEvent, UpdateTask (apenas armazenados)

* **CPaaS**: delivered/read/failure

* **IAM**: autenticação/autorização

Isso permite reconstruir **a linha do tempo completa da jornada** com precisão jurídico-regulatória.

# 14\. Aplicações Operacionais, Analíticas, Educacionais e Assistentes Virtuais

As aplicações da Plataforma Intellicare consomem o MCP e os repositórios institucionais (GC Cuidado e RSC-FHIR) por meio de APIs e serviços. Elas **não implementam lógica de jornada, não enviam mensagens diretamente, não escrevem no FHIR e não executam**.

O papel de cada classe de aplicação é definido a seguir.

## 14.1. CarePlanner — Aplicação Operacional Institucional

O **CarePlanner** é a principal interface operacional do BemCuidar EC.

**Funções**

✔ criar tarefas  
 ✔ atualizar tarefas  
 ✔ encerrar tarefas  
 ✔ gerar TaskEvent/UpdateTask  
 ✔ registrar conclusão de eventos de jornada  
 ✔ visualizar estado operacional e clínico via MCP  
 ✔ acionar ações recomendadas pelo MCP  
 ✔ interagir com a IA assistiva (Wanda)

**Não faz**

❌ enviar mensagens  
 ❌ ativar contextos MCP  
 ❌ aplicar protocolos MCP  
 ❌ registrar FHIR diretamente  
 ❌ decidir sobre a jornada

## 14.2. Painéis Operacionais e Analíticos (BemCuidar, MCP, Coordenação do Serviço)

✔ visão gerencial da jornada  
 ✔ indicadores de desempenho e qualidade  
 ✔ filas, prazos, riscos e pendências  
 ✔ indicadores APS  
 ✔ logs MCP e alertas  
 ✔ insights clínicos e operacionais

São exclusivamente **consumidores** dos dados do MCP, FHIR e GC Cuidado.

## 14.3. Simuladores de Cuidado e AOM-IA

✔ apoiar formação de enfermeiros e gerenciadores  
 ✔ simular decisões MCP  
 ✔ treinar protocolos e padrões da BCCO  
 ✔ avaliar competências

**Não fazem**

❌ modificar MCP  
 ❌ registrar dados reais  
 ❌ gerar evidências FHIR

## 14.4. Assistentes Virtuais

**Wanda — Assistente para Equipes**

✔ explica decisões do MCP  
 ✔ gera sínteses clínicas  
 ✔ ajuda a entender a jornada  
 ✔ apoia tomada de decisão (supervisionada)

**Geralda — Assistente para Pacientes/Família**

✔ envia orientações educativas  
 ✔ responde dúvidas simples  
 ✔ reforça protocolos institucionais

Ambas **nunca** atuam sem a supervisão do MCP nem enviam mensagens diretamente (somente via CPaaS por decisão do MCP).

## 14.5. Aplicações APS

✔ recebem notificações MCP (via CPaaS)  
 ✔ reportam retorno APS  
 ✔ visualizam orientações  
 ✔ interagem com equipe do hospital

**Não fazem**

❌ interpretar protocolos MCP  
 ❌ enviar mensagens diretas  
 ❌ manipular o RSC-FHIR

# 15\. Integração via RSC-FHIR e Mecanismos de Evidência

O **RSC-FHIR** é o repositório clínico institucional. Ele registra evidências assistenciais aplicadas pelo MCP.

Esta seção complementa — sem duplicar — a definição da Camada de Infraestrutura no documento Arquitetura Conceitual.

O MCP utiliza o RSC-FHIR para:

* obter estado clínico

* registrar evidências

* documentar decisões

* manter consistência assistencial

## 15.1. Padrões FHIR Utilizados

**Communication**

Mensagens enviadas a pacientes, APS ou familiares.

**AuditEvent**

Rastreia ações MCP:

* evento recebido

* contexto ativado

* protocolo aplicado

* ação executada

**Provenance**

Versionamento e autoria de recursos.

**Encounter**

Estados de internação (admit, discharge).

**Condition / Observation**

Estado clínico, sinais, sintomas.

**DocumentReference**

Materiais educativos, orientação, relatórios, sumários IA.

## 15.2. Funções do RSC-FHIR

✔ fonte oficial do estado clínico  
 ✔ registro institucional da jornada  
 ✔ base para auditoria  
 ✔ integração com RNDS  
 ✔ interoperabilidade entre sistemas

## 15.3. Integração MCP ↔ FHIR

O MCP:

* lê o estado clínico (Model)

* registra evidências de protocolos (Protocol)

* atualiza a linha do tempo (“clinical journey timeline”)

Exemplo:  
 No C21, MCP envia saudação → registra **Communication** \+ **AuditEvent**.

## 15.4. Integração CarePlanner ↔ FHIR

CarePlanner não escreve no FHIR.  
 Ele apenas:

* consome informações via MCP;

* envia eventos operacionais ao MCP, que decide o registro FHIR necessário.

## 15.5. Governança do FHIR

* qualquer alteração no schema exige aprovação do NGC \+ TI;

* novos tipos de Communication, DocumentReference ou AuditEvent precisam ser padronizados;

* versionamento de recursos é obrigatório.

# 16\. EventosJornadaEC como Componente do MCP

Os **EventosJornadaEC** representam marcos institucionais da Jornada de Internação do BemCuidar EC. Inicialmente concebidos como lógica do CarePlanner, foram **reposicionados corretamente** como **evento nativo da Máquina de Estados do MCP**, garantindo governança, explicabilidade, rastreabilidade e consistência institucional.

## 16.1. Por que EventosJornadaEC pertencem ao MCP

Eles devem ser parte do MCP porque:

* possuem **significado assistencial** (“previsão de alta registrada”, “orientação familiar”, “vínculo APS confirmado”, etc.);

* **ativam contextos** (C21, C22, C33, C23 etc.);

* são essenciais para a **linha do tempo assistencial**;

* demandam **protocolo institucional**;

* devem ser **auditáveis via FHIR** (AuditEvent, Communication, DocumentReference);

* precisam ser governados pelo **NGC**, não por uma aplicação;

* impactam **a jornada inteira**, não apenas uma tela ou módulo.

## 16.2. Tipos de EventosJornadaEC

A categoria "EventosJornadaEC" contém eventos institucionais de:

1. **admissão do serviço**

   * apresentação do serviço concluída

2. **articulação APS**

   * APS vinculada

   * APS indisponível

   * APS notificada

3. **educação familiar**

   * orientação realizada

   * material entregue

4. **dinâmica da internação**

   * reavaliação de risco

   * alteração clínica relevante

5. **programação de alta**

   * previsão de alta registrada

6. **desfecho internação**

   * alta hospitalar registrada

   * pós-alta iniciado

7. **encerramento da jornada**

   * jornada concluída

## 16.3. Estrutura Formal de um EventoJornadaEC

Todos os EventosJornadaEC possuem:

```
id
tipo
subtipo (quando aplicável)
timestamp
paciente_id
jornada_id
origem (profissional, APS, sistema)
payload contextual
responsável (quando humano)
unidade assistencial
```

Exemplo simplificado:

```
id: evt.apresentacao_servico.concluida
tipo: evento_jornada_ec
origem: careplanner
paciente_id: 123
unidade: enfermaria_5c
responsavel: enf_joana
timestamp: 2025-02-12T14:35:22Z
```

## 16.4. EventosJornadaEC e a Máquina de Estados MCP

Cada EventoJornadaEC:

* **chega ao Motor de Eventos**

* é **normalizado e enriquecido** pelo Model

* é interpretado pelo Context

* ativa um contexto específico

* aciona um Protocolo (Protocol Engine)

* gera **evidências formais**

Exemplo simples:

### **Evento: `apresentacao_servico.concluida`**

→ Estado: C1 ativo  
 → Contexto: **C21**  
 → Protocolo: boas-vindas, consentimento, canal ativo  
 → Evidências: Communication(FHIR), AuditEvent

## 16.5. EventosJornadaEC na Governança

Sob governança da Coordenação do Serviço BemCuidar EC:

* novos eventos são aprovados e versionados,

* mudanças exigem análise de impacto,

* protocolos associados são validados,

* a Matriz Evento→Contexto é atualizada,

* a BCCO é atualizada quando necessário,

* logs MCP e FHIR são revisados durante auditorias.

## 16.6. Impacto Estratégico do Reposicionamento

O reposicionamento dos EventosJornadaEC como parte do MCP:

* garante **padronização institucional**,

* elimina lógica duplicada nas aplicações,

* fortalece **auditoria** e **explicabilidade**,

* simplifica o CarePlanner (aplicação),

* melhora a integração hospital–APS,

* viabiliza expansão para novas jornadas sem reescrever aplicações.

# 17\. Catálogo Institucional MCP

O **Catálogo Institucional MCP** é o documento mestre que define:

* todos os **eventos** reconhecidos pelo MCP,

* todos os **contextos** existentes,

* todos os **protocolos** associados,

* o mapeamento determinístico **Evento → Contexto → Protocolo**.

Ele é essencial para:

* implementação técnica,

* formação profissional,

* auditoria,

* governança clínica,

* expansão do MCP para outras jornadas,

* articulação com APS.

## 17.1. Estrutura do Catálogo MCP

O catálogo possui três grandes seções:

### A) Eventos MCP

* tipo

* origem

* critérios de ativação

* regras de idempotência

* parâmetros obrigatórios

### B) Contextos MCP

* tipo (Clínico, Digital, Operacional, Governança, Interativo)

* gatilhos

* pré-condições

* protocolos associados

* dependências

* pontos de encerramento

### C) Matriz Evento → Contexto → Protocolo → Ações

* cada linha representa um fluxo institucional determinístico

* é a coluna vertebral da Máquina de Estados MCP

## 17.2. Catálogo Inicial (PoC C1—C21—C22—C12)

**Contextos incluídos na PoC:**

* **C1 — Paciente Internado (reduzido)**

* **C21 — Engajamento Digital Inicial Paciente**

* **C22 — Engajamento Digital Inicial APS**

* **C12 — Conversa Inbound**

**Eventos incluídos na PoC:**

* `evt.apresentacao_servico.concluida`

* `evt.vinculo_aps.confirmado`

* `evt.msg.inbound`

* `evt.msg.delivered`

* `evt.msg.failed`

**Exemplo de linha da Matriz MCP (PoC)**

| Evento | Estado | Contexto | Protocolo | Ações | Evidências |
| ----- | ----- | ----- | ----- | ----- | ----- |
| apresentação\_serviço.concluída | C1 ativo | C21 | boas-vindas | CPaaS envia mensagem; TaskEvent; consentimento | Communication; AuditEvent |

## 17.3. Governança do Catálogo MCP

O catálogo é governado pela tríade:

* **Coordenação do Serviço BemCuidar EC**,

* **TI / Arquitetura** (viabilidade técnica),

* **Privacidade / Compliance** (segurança, LGPD),

* **APS** (fluxos intersetoriais), quando aplicável.

Mudanças exigem:

1. Avaliação do impacto clínico e institucional

2. Revisão da Máquina de Estados

3. Atualização da BCCO

4. Ajuste de protocolos

5. Versionamento

6. Treinamento da equipe (AOM-IA)

## 17.4. O Catálogo como Instrumento de Expansão

Cada nova jornada (crônicos, oncologia, paliativo, cirúrgico) terá:

* novos contextos

* novos eventos

* novos protocolos

* novas matrizes

Sem impactar a jornada existente — exatamente por causa da separação entre contexto e aplicação.

# 18\. Mecanismos de Explicabilidade e Auditoria MCP

O MCP é projetado com **explicabilidade total** e **auditoria ponta a ponta** como premissas fundamentais.  
 Cada decisão pode ser reconstruída:

* o que aconteceu,

* em que contexto,

* com qual estado,

* por qual protocolo,

* gerando qual ação,

* com qual evidência.

## 18.1. Princípios de Explicabilidade

**1\. Nenhuma decisão sem justificativa**

Cada ação é explicável via Model, Context e Protocol.

**2\. Nenhuma ação automática sem contexto**

O MCP só age dentro de um contexto ativo.

**3\. IA sempre supervisionada**

IA sugere, MCP decide.

**4\. Linha do tempo completa**

Todos os eventos e decisões são registradas.

**5\. Transparência para profissionais**

A assistente Wanda pode explicar cada decisão.

## 18.2. Mecanismos de Auditoria

**1\) AuditEvent (FHIR)**

Registra cada ação do MCP.

**2\) Provenance (FHIR)**

Versiona e identifica autoria.

**3\) Communication (FHIR)**

Formaliza conteúdos enviados ao paciente/APS.

**4\) GC Cuidado**

Armazena TaskEvents/UpdateTasks originados do MCP.

**5\) Logs MCP**

Registram pipeline de eventos, idempotência e exceções.

**6\) Logs CPaaS**

Registram status digital (entregue, falha, leitura).

**7\) Logs IAM**

Registram autenticação, autorização e tentativas.

## 18.3. Linha do Tempo Assistencial Integrada (“Journey Audit Trail”)

A jornada é reconstruída via combinação de:

* eventos brutos,

* contextos ativados,

* ações MCP,

* mensagens CPaaS,

* tarefas CarePlanner,

* registros clínicos FHIR.

Exemplo:

```
1. Encounter.admit
2. apresentação_serviço.concluída
3. [C21] boas-vindas enviadas
4. APS vinculada → [C22] notificação APS
5. mensagem inbound → [C12] triagem e tarefa
6. previsão alta registrada → [C33] programação alta
...
```

## 18.4. Explicabilidade para Profissionais (Wanda)

Wanda pode responder:

* “Por que o MCP enviou esta mensagem?”

* “Que evento disparou essa ação?”

* “Por que a IA classificou a mensagem dessa forma?”

* “Quais evidências justificam este contexto?”

## 18.5. Explicabilidade e Segurança da IA

Cada interação IA contém:

* input

* output

* versão do modelo

* justificativa

* registro em FHIR (quando assistencial)

* avaliação MCP

Sempre supervisionada.

## 18.6. Propósito Institucional da Explicabilidade

* segurança do paciente

* conformidade LGPD

* transparência

* confiança das equipes

* pesquisa e ensino

* melhoria contínua do serviço

* defesa jurídico-regulatória

# 19\. Conexão com a Jornada BemCuidar

A Jornada BemCuidar EC é o **processo assistencial institucional** que organiza o cuidado do paciente durante a internação hospitalar e na transição para o domicílio, articulando equipe hospitalar, paciente, família e APS.

O MCP Intellicare se acopla à Jornada BemCuidar de forma **não intrusiva**, **sem substituir o trabalho da equipe**, mas garantindo:

* coerência da jornada,

* supervisão da IA,

* padronização,

* explicabilidade,

* integração com APS,

* acionamento oportuno de protocolos,

* registro de evidências.

## 19.1. Estágios da Jornada BemCuidar e Acoplamento MCP

Os estágios institucionais da jornada são:

1. **Triagem e Identificação**

2. **Admissão e Apresentação do Serviço**

3. **Cuidados Durante Internação**

4. **Programação de Alta**

5. **Desfecho Internação (ex.: Alta Médica / Transição)**

6. **Cuidado Pós-Alta e Acompanhamento**

7. **Conclusão da Jornada**

Para cada estágio, o MCP:

* **recebe eventos**,

* **interpreta o estado da jornada**,

* **ativa o contexto apropriado**,

* **executa protocolos** da BCCO,

* **registra evidências** em FHIR e GC Cuidado.

## 19.2. Mapeamento Estágio → Evento → Contexto

**1\) Triagem e Identificação**

* Evento: Encounter.admit

* Contexto: **C1 — Paciente Internado (Raiz)**

* Protocolo: iniciar jornada, registrar admissão

**2\) Apresentação do Serviço**

* Evento: apresentação\_serviço.concluída

* Contexto: **C21 — Engajamento Digital Inicial**

* Protocolo: boas-vindas, consentimento, canal

→ Se APS vinculada: ativa **C22**

**3\) Cuidados Durante a Internação**

Eventos:

* msg.inbound (paciente/família) → **C12**

* orientação familiar → **C23**

* risco clínico alterado → **C51**

**4\) Programação de Alta**

* Evento: previsão\_alta.registrada

* Contexto: **C33 — Programação de Alta**

**5\) Desfecho Internação**

* Evento: Encounter.discharge

* Contexto: **C41 — Alta Clínica**

**6\) Cuidado Pós-Alta**

Eventos:

* msg.inbound → **C12**

* sintomas → **C51**

* vínculos APS → **C72**

Contextos:

* **C52 — Acompanhamento Pós-Alta**

**7\) Conclusão da Jornada**

* Evento sintético: jornada.encerrada

* Contexto: **C99 — Encerramento Institucional**

## 19.3. Papel da APS na Jornada BemCuidar via MCP

A APS participa:

* na admissão (C22),

* na programação da alta (C33),

* no cuidado pós-alta (C52),

* na conclusão da jornada (C99).

O MCP garante:

* notificação padronizada,

* explicabilidade,

* substituição segura quando APS não responde (C72).

## 19.4. Benefícios da Integração MCP–Jornada

* padronização da comunicação

* menos variabilidade assistencial

* transição mais segura

* engajamento digital estruturado

* melhor integração com APS

* auditoria ponta a ponta

* menor retrabalho para a equipe

* redução de riscos assistenciais

# 20\. Roadmap Técnico MCP

O Roadmap do MCP segue 4 ondas evolutivas:

### **✅ Nível 0 — Preparação**

### **🚀 Nível 1 — PoC MCP**

### **🧩 Nível 2 — MVP MCP v1**

### **🌐 Nível 3 — Jornada Completa de Internação**

### **🔭 Nível 4 — Expansão Multijornada**

## 20.1. Nível 0 — Preparação (Pré-PoC)

Infraestrutura mínima:

* MCP

* RSC-FHIR

* CPaaS

* GC Cuidado

* IAM

* BCCO v0.1

* Catálogo MCP mínimo

* Templates CPaaS aprovados

* Acordo institucional (NGC)

## 20.2. Nível 1 — PoC MCP (C1 reduzido \+ C21 \+ C22 \+ C12)

**Objetivo:**

Validar o funcionamento mínimo do MCP:

* ativação de contextos

* execução de protocolos

* integração CPaaS

* evidências em FHIR

* tarefas no CarePlanner

* IA supervisionada

* linha do tempo auditável

**Escopo da PoC:**

* **C1** (reduzido)

* **C21**

* **C22**

* **C12**

**Critérios de Sucesso:**

* mensagens entregues corretamente

* tarefas criadas corretamente

* logs MCP consistentes

* decisão determinística

* equipe compreende e valida comportamentos

## 20.3. Nível 2 — MVP MCP v1

Expansão para:

* C23 (Educação Familiar)

* C33 (Pré-Alta)

* C51 (Triagem Sintomas)

* C52 (Pós-Alta)

* C41 (Alta Clínica)

* C72 (Problema APS)

Outros entregáveis:

* BCCO com conteúdos clínicos completos

* painéis MCP

* integração APS fase 1

* segurança reforçada (ABAC, logs, IAM avançado)

## 20.4. Nível 3 — Jornada Completa de Internação

Capacidades adicionadas:

* reavaliações

* falhas APS e fallback

* protocolos multievento

* restrições temporais

* IA avançada

* integração Tasy → Mirth → FHIR

* auditoria institucional completa

## 20.5. Nível 4 — Expansão Multijornada

Jornadas futuras:

* Crônicos (DM, HAS, DRC, IC)

* Oncologia

* Paliação

* Cirurgia

* Longitudinal por condição

* Saúde mental

* Pediatria complexa

Cada jornada adiciona novos contextos sem quebrar as anteriores.

# 21\. Conclusão e Encaminhamentos

O MCP Intellicare representa um avanço decisivo para o HDG na direção de:

* governança assistencial avançada,

* coordenação segura da jornada,

* integração hospital–APS,

* uso supervisionado e seguro de IA,

* explicabilidade institucional,

* redução de riscos assistenciais,

* melhoria de desfechos clínicos.

## 21.1. Síntese Institucional

Com o MCP, o Hospital SUS:

* centraliza lógica de cuidado,

* elimina dependência de aplicações,

* padroniza a jornada,

* possibilita replicação regional,

* incorpora IA de forma ética e segura.

A Jornada BemCuidar torna-se:

* explicável,

* auditável,

* interoperável,

* escalável,

* institucionalmente governada,

* centrada no paciente e na família.

## 21.2. Encaminhamentos Institucionais

**1\. Aprovação pela Engenharia do Cuidado/HDG**

* catálogo MCP inicial

* protocolos

* templates

* escopo da PoC

**2\. Preparação Técnica (TI \+ APS \+ BemCuidar)**

* infraestrutura mínima

* integração CPaaS

* ativação IAM

* publicação FHIR

* configurações MCP

**3\. Execução da PoC**

* 10 pacientes

* acompanhamento diário

* logs MCP

* análise NGC

* ajustes incrementais

**4\. Decisão (Go/No-Go)**

* evolução para MVP MCP v1

## 21.3. Fecho Institucional

O MCP Intellicare é:

“A camada inteligente, governável e auditável que garante segurança, consistência e continuidade da jornada assistencial — articulando hospital, APS, pacientes, famílias e IA.”