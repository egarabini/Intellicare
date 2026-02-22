# Base de Conhecimento Clínico e Operacional \- Documento Técnico

1. # Finalidade da Camada de Conhecimento

A **Base de Conhecimento Clínico e Operacional** é a camada responsável por armazenar, organizar, versionar e disponibilizar o conhecimento que fundamenta:

* as decisões assistenciais (protocolos clínicos, diretrizes, pathways);

* as decisões operacionais (protocolos de coordenação do cuidado, fluxos de transição, critérios de risco);

* o funcionamento dos **Serviços de Inteligência** e do **Núcleo MCP (Model–Context–Protocol)**;

* o trabalho dos assistentes virtuais e copilotos de IA (por exemplo, Wanda atuando na elaboração de planos de cuidado personalizados).

Essa camada garante que as recomendações geradas pela Plataforma Intellicare estejam alinhadas às **fontes institucionais de verdade clínica e operacional**, e não apenas à “opinião” do modelo de IA.

2. # Escopo do Conteúdo da Base de Conhecimento

A base de conhecimento abrange, pelo menos, os seguintes tipos de conteúdo:

1. **Protocolos clínicos institucionais**

   * Protocolos adotados pelo hospital para condições específicas (ex.: IC, DRC, oncologia, paliativo).

   * Algoritmos de decisão (por exemplo, critérios de elegibilidade, estratificação de risco, intervenções padrão).

2. **Diretrizes e pathways assistenciais**

   * Linhas de cuidado institucionais e/ou regionais.

   * Mapas de jornada com etapas, responsabilidades e critérios de transição.

3. **Protocolos operacionais de coordenação do cuidado**

   * Regras para acompanhamento pós-alta, follow-up, escalonamento, transição entre níveis de atenção.

   * Critérios para acionamento da APS, telessaúde, equipes de suporte, etc.

4. **Terminologias, ontologias e mapeamentos**

   * CID-10, LOINC, SNOMED CT (quando aplicável), TUSS e outros códigos relevantes.

   * Tabelas de mapeamento entre códigos internos e padrões externos.

5. **Modelos e templates de Plano de Cuidado**

   * Estruturas de CarePlan, templates por condição clínica, listas de intervenções sugeridas.

   * Elementos de educação em saúde e determinantes sociais relevantes.

6. **Conhecimento operacional da plataforma**

   * Definições padronizadas de eventos, estados de jornada, tipos de tarefas, categorias de risco.

Essa base deve ser vista como **um ativo institucional**, com governança clínica e técnica.

3. # Integração com o MCP e com os Serviços de Inteligência

   1. ## Relação com o Núcleo MCP

A Camada de Conhecimento alimenta os três módulos do MCP:

* **Model**:

  * Usa terminologias e mapeamentos para interpretar dados clínicos e sociais do paciente (FHIR \+ GC Cuidado).

  * Acessa definições de condições clínicas, critérios de classificação e perfis de pacientes.

* **Context**:

  * Utiliza regras e pathways para reconhecer em que ponto da jornada o paciente se encontra.

  * Apoia a lógica de “se X e Y, então este é o contexto Z”.

* **Protocol**:

  * Usa protocolos clínicos e operacionais, representados de forma estruturada (regra, fluxo, guideline) para sugerir intervenções, atualizar CarePlans e definir tarefas.

  * Conecta o conhecimento institucional à automação de decisões assistenciais e de coordenação.

  2. ## Relação com os Serviços de Inteligência e IA (incluindo Wanda)

Os Serviços de Inteligência e os assistentes virtuais (como Wanda) interagem com a Base de Conhecimento para:

* **Elaborar planos de cuidado personalizados**

  * Partindo das condições clínicas (RSC FHIR), determinantes sociais e preferências do paciente;

  * Recuperando protocolos relevantes na Base de Conhecimento;

  * Gerando sugestões de cuidado alinhadas à prática institucional.

* **Responder dúvidas clínicas e operacionais**

  * Com base em protocolos institucionais, e não apenas em conhecimento genérico da IA.

A tecnologia exata (RAG, rule engine, modelos híbridos etc.) poderá evoluir ao longo do tempo, mas a **camada de conhecimento se mantém como fonte estruturada e auditável**.

4. # Tecnologias para Implementação da Base de Conhecimento

A arquitetura da Base de Conhecimento deve ser **agnóstica em relação à tecnologia de IA**, mas preparada para diferentes modos de consumo (RAG, regras, consultas diretas). A seguir, uma visão por camadas tecnológicas.

1. ## Camada de Armazenamento de Conteúdo

* **Repositório de documentos** (ex.: armazenamento de arquivos em formato estruturado: Markdown, HTML, JSON, FHIR Library, PlanDefinition):

  * Pode residir em storage de objetos (ex.: S3 compatível, MinIO) ou em tabelas específicas no PostgreSQL.

* **Base relacional ou documental para metadados**:

  * PostgreSQL (aproveitando infraestrutura já utilizada pelo GC Cuidado e Lakehouse) para:

    * Versionamento;

    * Metadados (especialidade, data, autor, status de aprovação, validade);

    * Vínculo com códigos CID-10, SNOMED CT, LOINC etc.

* **Mecanismo de busca full-text**:

  * Ferramentas como Elasticsearch/OpenSearch ou recursos nativos de busca do PostgreSQL.

  * Indexação de protocolos, guidelines e materiais educativos.

* **(Opcional) Banco de vetores para IA (RAG)**:

  * Uso de extensões como **pgvector** (no próprio PostgreSQL) ou bases de vetores especializadas.

  * Permite que serviços de IA recuperem trechos relevantes de documentos com base em semelhança semântica.

  2. ## Representação Estruturada do Conhecimento

* **Recursos FHIR para conhecimento clínico**

  * *PlanDefinition, ActivityDefinition, Library* e perfis relacionados podem representar protocolos e planos em formato computável.

  * Iniciativas como **CPG-on-FHIR** podem ser referência para modelagem futura de guidelines computáveis.

* **Ontologias e terminologias**

  * Servidor de terminologia (FHIR Terminology Server ou equivalente) para SNOMED, LOINC, CID-10 etc.

  * Mapeamentos mantidos em tabelas do PostgreSQL, com APIs para consulta.

* **Regras e fluxos**

  * Representação em BPMN, DMN ou linguagens de regras, caso se opte por um **motor de regras** para partes do protocolo.

5. # Tecnologias de IA e Padrões de Consumo do Conhecimento

A Base de Conhecimento deve estar pronta para ser consumida por diferentes arquiteturas de IA:

1. ## RAG (Retrieval-Augmented Generation)

* Os serviços de IA, incluindo Wanda, recebem:

  * O contexto do paciente (dados estruturados do Model);

  * O contexto da jornada (Context);

  * Uma consulta à Base de Conhecimento.

* O mecanismo RAG:

  * Converte a pergunta/necessidade em embeddings;

  * Recupera trechos relevantes dos protocolos;

  * Gera uma resposta (plano de cuidado, orientações, checklist) **citando ou respeitando o conteúdo recuperado**.

  2. ## Motores de Regras (Rule Engines)

* Partes dos protocolos podem ser traduzidas em regras (if/then) e executadas por um motor de regras:

  * Ex.: critério para classificar risco, indicar encaminhamento, acionar fluxo específico.

  3. ## Modelos Híbridos

* Combinações de regras, RAG e modelos especializados podem ser usadas conforme o tipo de decisão:

  * Regras rígidas para decisões de alto impacto regulatório;

  * RAG para recomendações, explicações e planos textuais;

  * LLMs especializados para sumarização e comunicação.

A Base de Conhecimento é desenhada para **suportar todas essas abordagens**, sem se acoplar a uma tecnologia específica de IA.

6. # Governança da Base de Conhecimento

A camada de conhecimento exige governança própria, articulada com a camada de Segurança, Privacidade e Governança (LGPD):

* **Fluxo de elaboração, revisão e aprovação**

  * Profissionais de referência (especialidades, comissões) elaboram ou propõem protocolos;

  * Comitê técnico-assistencial revisa;

  * Versões aprovadas são publicadas na Base de Conhecimento.

* **Versionamento e rastreabilidade**

  * Toda alteração gera nova versão;

  * Histórico com data, autor, justificativa e status (proposta, em revisão, válida, obsoleta).

* **Rastreabilidade nas recomendações de IA**

  * As recomendações geradas por IA ou pelo MCP devem ser explicáveis:

    * “Com base no Protocolo de Insuficiência Cardíaca – Versão 1.3, item X”.

* **Integração com LGPD e ética**

  * A base não armazena dados identificáveis de pacientes;

  * Concentra-se em conhecimento clínico/operacional, não em dados pessoais.

7. # Visão Funcional da Aplicação de Gestão de Conhecimento 

   1. ## Propósito da Aplicação

A aplicação de Gestão de Conhecimento (Knowledge Manager) é o sistema responsável por **criar, editar, versionar, validar, aprovar, publicar e retirar de circulação** os conteúdos da Camada de Conhecimento Clínico e Operacional, garantindo:

* governança e consistência institucional,  
* versionamento e auditoria,  
* atualização contínua,  
* disponibilização padronizada para MCP e Serviços de Inteligência (Wanda, copilotos, síntese clínica, recomendações, etc.).

A aplicação é voltada para **profissionais especialistas**, **gestores clínicos**, **comissões assistenciais** e a equipe da Plataforma Intellicare.

2. ## Visão Funcional Aplicação Gestão do Conhecimento

   1. ### Funcionalidades Principais

### **(a) Cadastro e edição de Protocolos Clínicos**

* Editor de conteúdo com suporte a:  
  * texto estruturado (Markdown, HTML simples);  
  * tabelas;  
  * listas de intervenções;  
  * passos de pathway;  
  * anexos;  
  * links para fontes externas (evidências, guidelines).  
* Estruturas sugeridas:  
  * Indicações;  
  * Critérios diagnósticos;  
  * Critérios de risco;  
  * Intervenções recomendadas;  
  * Condicionantes e exceções;  
  * Critérios de transição de cuidado.

### **(b) Gestão de Protocolos Operacionais**

* Cadastro de fluxos de coordenação (triagem, planejamento, coordenação, conclusão).  
* Critérios para escalonamento.  
* Regras para follow-up e contato.  
* Padrões de tarefas e estados operacionais.

### **(c) Versionamento Avançado**

Cada protocolo possui:

* número de versão,  
* autor,  
* data de criação,  
* revisores,  
* mudanças realizadas (changelog),  
* status (rascunho / em revisão / aprovado / publicado / obsoleto).

Regras importantes:

* publicações não podem ser alteradas — apenas revisadas;  
* versões antigas permanecem disponíveis para auditoria;  
* o MCP e os Serviços de Inteligência sempre usam a **versão vigente**.

### **(d) Workflow de Revisão e Aprovação**

Fluxo recomendado:

1. **Proposta** (autor cria rascunho)  
2. **Revisão técnica** (especialista clínico / área responsável)  
3. **Revisão institucional** (comissão, superintendência assistencial)  
4. **Aprovação**  
5. **Publicação**  
6. **Vigilância ativa** (avaliação periódica ou conforme evidências novas)

Com notificações e registros de quem aprovou e quando.

### **(e) Ligação com Terminologias e Ontologias**

A aplicação deve permitir:

* vincular um protocolo a códigos **CID-10**, **SNOMED CT**, **LOINC**, **TUSS**,  
* associar intervenções a códigos FHIR (*ActivityDefinition*, *PlanDefinition*),  
* estruturar partes do conhecimento para consumo automático por IA.

### **(f) Publicação para Consumo por MCP e IA**

A aplicação deve oferecer **APIs de consulta** que permitam:

* buscar protocolo por condição clínica, código CID-10, ou palavra-chave;  
* recuperar trechos específicos (Indicações, Critérios, Intervenções);  
* buscar pathways completos;  
* disponibilizar conteúdos estruturados para:  
  * **RAG (Retrieval-Augmented Generation)**;  
  * **motores de recomendação**;  
  * **PlanDefinition/ActivityDefinition FHIR**;  
  * **Wanda** e copilotos;  
  * **MCP – Módulo Protocol**.

APIs recomendadas:

* `/knowledge/search`  
* `/knowledge/protocols/{id}`  
* `/knowledge/current/{cid}`  
* `/knowledge/suggestions/careplan`

### **(g) Indexação e Busca Semântica**

* Indexação full-text.  
* Indexação de embeddings para IA (via pgvector).  
* Permitir que Wanda recupere trechos relevantes para personalizar recomendações.

### **(h) Governança e Auditoria**

* Registro de todas as ações (criar, editar, revisar, aprovar, publicar).  
* Histórico completo por usuário.  
* Exportabilidade para auditoria institucional ou regulação.

  2. ### Perfis de Usuário

* **Autor Clínico**  
   Cria conteúdos e sugere atualizações.  
* **Revisor Técnico**  
   Valida alinhamento científico.  
* **Aprovador Institucional**  
   Autoriza publicação.  
* **Administrador da Base**  
   Gerencia versões, acessos e regras de revisão.  
* **Consumidores automáticos (MCP, IA, Wanda)**  
   Não acessam a aplicação, apenas as APIs.

  3. ## Arquitetura Aplicada

     1. ### Backend

* PostgreSQL (estrutura \+ pgvector)  
* APIs REST padronizadas  
* Representações FHIR (*PlanDefinition*, *Library*) opcionais  
* Integração com servidor de terminologias

  2. ### Frontend

* Interface web responsiva com foco em UX para clínicos

  3. ### Segurança

* Controle de acesso via Keycloak (RBAC/ABAC)  
* Auditoria obrigatória  
* Minimização de dados — *não armazenar dados de pacientes* na camada

  4. ## Benefícios da Aplicação

* Uniformiza e institucionaliza o conhecimento clínico-operacional  
* Evita dependência do “conhecimento tácito” dos profissionais  
* Permite explicabilidade das recomendações geradas por IA  
* Garante rastreabilidade e auditoria  
* Reduz risco clínico e jurídico  
* Facilita atualizações dos protocolos  
* Conecta diretrizes institucionais ao MCP e à IA