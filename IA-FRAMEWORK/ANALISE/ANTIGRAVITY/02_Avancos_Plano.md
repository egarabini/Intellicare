# Proposta de Avanço para a Plataforma INTELLICARE e Plano de Implementação

Com base na abordagem *AIOX/Squads* analisada, existem paradigmas altamente inovadores aplicáveis ao **INTELLICARE** que poderiam elevar significativamente sua inteligência artificial e capacidade resolutiva.

## 1. O Avanço: "Clinical Squads" & Roteamento Hierárquico

Atualmente, o **IntelliCare** concentra muito da inteligência no módulo de `cuidado` baseando-se em RAG (via pgvector) + SLM interagindo com protocolos do módulo `florence`. A inspiração do AIOX nos sugere construir um formato de **Roteamento Clínico (Clinical Squads)** semelhante aos Tiers deles.

Em vez de enviar a requisição do paciente (ex: Check-in CarePlanner ou Mensagem via Evolution) para um fluxo linear de decisão, poderíamos estabelecer:
* **Tier 0 (Acolhimento/Triagem)**: O "Chief". Recebe a mensagem do Listmonk/WhatsApp e decide se o caso é suporte técnico, anamnese preliminar ou emergência clínica.
* **Tier 1 (Especialistas Clínicos)**: Se diagnosticado risco moderado, invoca-se o Especialista base (baseado nos dados do módulo Florence).
* **Tier 2 (Pesquisadores)**: Chamadas aos artefatos avançados do `pgvector` para consolidar o histórico completo (Vault).
* **Tier 3 (QA Audit)**: Validação do módulo Oswaldo para garantir que a saída obedece as seguranças de HL7 FHIR e as restrições médicas cadastradas antes de retornar ao paciente.

### O grande diferencial: "Health DNA" vs "Voice DNA"
Assim como o AIOX clona o conhecimento de experts via *Voice DNA* nos seus manifestos, o IntelliCare poderia encapsular os POPs (Procedimentos Operacionais Padrão) em manifestos `.yaml` de comportamento rígido de IA, garantindo que o bot da clínica X responde diferente do bot da clínica Y embasado em heurísticas fixas (sem variações aleatórias na IA).

---

## 2. Plano de Implementação (Roadmap Resumido)

O foco da implementação será manter o **Desacoplamento** entre módulos atuais (`careplanner`, `florence`, `oswaldo`) e o **Isolamento de Tenant**, exigências chave do sistema.

### Fase 1: Arquitetura Base do "Clinical Squad" (Módulo CarePlanner + Florence)
1. **Definir o Manifesto Squad (YAML/JSON)**: Especificar perfis rigorosos (Enfermeiro IA, Nutricionista IA, Médico Generalista IA) mapeando suas *Heurísticas* e *Limites* em estruturas Pydantic no `intellicare-core`.
2. **Setup do Orchestrator/Chief**: Refatorar o listener de WhatsApp e Email (vistos nas DEM-047/048) para encaminhar as respostas de pacientes a um "Chief Agent".
3. **Mock de Decisão**: O Chief Agent faz a primeira requisição ao LLM (SLM), classificando a intenção clínica com um fallback seguro.

### Fase 2: Implementando o Quality Gate (Módulo Oswaldo)
1. Estabelecer o padrão de que nenhuma resposta de "Tier 1/2" é enviada ao adaptador (`EmailAdapter/WhatsAppAdapter`) sem passar por um Gatekeeper.
2. O Gatekeeper avalia periculosidade (palavras de risco, emergência identificável) rodando uma restrição forte baseada na R4 FHIR, barrando "alucinações" médicas.

### Fase 3: Instrumentação do Context Contextual
1. Adotar a ideia de "Story-Driven" do AIOX porém para "Caso-Driven" (Timeline).
2. O agente não recebe uma janela de texto limpa. Ele recebe um *"Documento Resumo do Caso"* gerado ativamente por scripts RAG antes do raciocínio e o agente só propõe a **próxima ação**. A memória e a história ficam versionadas, e não perdidas nos logs do Chat.

### Benefício Final Esperado
Uma arquitetura onde cada paciente não fala com um "chatbot genérico da plataforma", mas aciona a **borda de um departamento de inteligência clínica (Squad)** que roteia a dor dele, submete o raciocínio a auditorias em paralelo, pesquisa o protocolo (`florence`) antes de autorizar a ida ao WhatsApp do usuário final. Alta determinabilidade, rastreabilidade plena via logs de "Worktrees Clínicos" e escala vertical e segura em ambientes de TI em Saúde.
