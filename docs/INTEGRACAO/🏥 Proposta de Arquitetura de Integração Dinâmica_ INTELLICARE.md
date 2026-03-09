# 🏥 Proposta de Arquitetura de Integração Dinâmica: INTELLICARE

Esta proposta detalha a estratégia para integrar o **INTELLICARE** com os principais sistemas de gestão hospitalar (HIS) do mercado brasileiro (**Philips Tasy, SOUL MV, Pixeon, SisHOSP, TOTVS e Feegow**), utilizando como referência técnica o padrão **SMART on FHIR** implementado no **OpenEMR**.

---

## 1. Estrutura de Integração Dinâmica (Core Architecture)

Para garantir uma integração que não quebre a cada atualização dos HIS e que seja escalável, propomos uma arquitetura baseada em **Adaptadores de Interoperabilidade** e um **Barramento FHIR Nativo**.

### 1.1. Camada de Abstração (The Adapter Pattern)
Em vez de criar uma integração específica para cada hospital, o INTELLICARE deve operar sobre uma **Canonical Data Model (CDM)** baseada em **HL7 FHIR R4**.

| Componente | Função |
| :--- | :--- |
| **IntelliCare FHIR Server** | Repositório central de dados padronizados (Single Source of Truth). |
| **HIS Adapters** | Microserviços que traduzem APIs proprietárias (ex: Feegow REST, TOTVS RM) para FHIR. |
| **SMART Proxy** | Camada que gerencia a autenticação OAuth2 e o contexto da sessão (EHR Launch). |

### 1.2. Referência OpenEMR: SMART on FHIR
O OpenEMR utiliza o padrão **SMART v2.2.0**, que devemos replicar para permitir o "EHR Launch":
- **EHR Launch:** O médico abre o INTELLICARE dentro do Tasy/MV sem precisar logar novamente.
- **Context Awareness:** O INTELLICARE recebe automaticamente o `patient_id` e `encounter_id` do sistema de origem.
- **Scopes Granulares:** Permissões específicas (ex: `patient/Observation.read`) para garantir segurança e conformidade com a LGPD.

---

## 2. Estratégia por Player (Market Mapping)

Cada sistema possui um nível de maturidade digital diferente. Nossa abordagem será híbrida:

| Sistema | Método de Integração | Status do Padrão |
| :--- | :--- | :--- |
| **Philips Tasy** | API HTML5 / Web Services (SOAP/REST) | Suporta FHIR em versões recentes. |
| **SOUL MV** | Plataforma de Interoperabilidade MV | Foco em barramento de serviços e FHIR. |
| **TOTVS (RM)** | API REST (TOTVS Developers) | APIs bem documentadas, mas proprietárias. |
| **Feegow** | REST API v1.0 (Token-based) | Simples, focada em JSON proprietário. |
| **Pixeon / SisHOSP** | Barramento Integrador / APIs Locais | Requer adaptadores específicos para extração. |

---

## 3. Diferenciais Avançados: Tornando a Plataforma "Estado da Arte"

Para ir além de uma simples ferramenta de gestão e se tornar um **Ecossistema de Inteligência Clínica**, sugerimos a inclusão dos seguintes módulos:

### 3.1. Orquestração de Agentes de IA (Multi-Agent System)
- **Agente de Alta Segura:** Analisa automaticamente a evolução clínica e sinaliza se o paciente cumpre os critérios de alta (evitando reinternações).
- **Agente de Reconciliação:** Cruza a prescrição hospitalar com o histórico prévio do paciente via RAG (Retrieval-Augmented Generation) para evitar erros de medicação.

### 3.2. Digital Twin do Paciente
- Criar uma representação digital que simula a trajetória de recuperação pós-alta, alertando a equipe de Home Care sobre desvios de normalidade antes que ocorra uma intercorrência.

### 3.3. Integração com Dispositivos Wearables (IoMT)
- Captura de sinais vitais (Apple Health, Google Fit, Oura) integrada diretamente ao recurso FHIR `Observation`, permitindo monitoramento remoto em tempo real no pós-alta.

### 3.4. Motor de Regras Clínicas (CDS Hooks)
- Implementar **CDS Hooks** para que o INTELLICARE possa "injetar" cards de recomendação dentro do prontuário do médico (ex: "Este paciente tem alto risco de queda no domicílio, deseja prescrever fisioterapia motora?").

---

## 4. Próximos Passos Recomendados

1. **MVP de Tradução:** Desenvolver o primeiro adaptador (ex: Feegow -> FHIR) para validar o fluxo de dados.
2. **Sandbox SMART:** Configurar um ambiente de testes que simule o "EHR Launch" para demonstrar aos hospitais a fluidez da experiência do usuário.
3. **Certificação de Segurança:** Garantir que a camada de integração esteja em conformidade com a **LGPD** e padrões de segurança (OAuth2/OpenID Connect).

---
*Documento gerado para a estratégia INTELLICARE - Março 2026*
