# Documento de Diretrizes de Desenvolvimento - Painel DRC (Protótipo)

**Projeto:** Painel DRC (Protótipo)
**Versão:** 1.0
**Data:** 30 de Janeiro de 2026
**Arquiteto:** [Nome do Usuário]
**Planejador:** Manus AI

Este documento estabelece as diretrizes e padrões técnicos que devem ser seguidos por todos os "Desenvolvedores" (ferramentas de IA como Claude, GPT, etc.) envolvidos na criação do protótipo do Painel DRC. O objetivo é garantir a consistência, a manutenibilidade e a conformidade com os padrões de saúde.

## 1. Filosofia do Projeto

O desenvolvimento do Painel DRC será guiado por dois princípios fundamentais:

### 1.1. Model First (FHIR)
A **modelagem dos dados** deve preceder a codificação. Isso significa que a estrutura dos recursos FHIR (Patient, Observation, Condition, etc.) e a definição dos *Profiles* específicos para a Doença Renal Crônica (DRC) são a prioridade. O código deve ser escrito para se adequar ao modelo de dados FHIR, e não o contrário.

### 1.2. API First
O Painel DRC será um **cliente** que consome uma API (o Servidor FHIR). O código deve ser modular, garantindo que a lógica de apresentação (Streamlit) esteja completamente desacoplada da lógica de acesso aos dados (FHIR Client). Isso permitirá a troca futura do Servidor FHIR (ex: de HAPI para Google Cloud Healthcare API) sem reescrever o painel.

## 2. Stack Tecnológico Principal

A base do projeto será o ecossistema Python, utilizando as seguintes ferramentas:

| Componente | Tecnologia | Propósito |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.11+ | Linguagem principal para desenvolvimento. |
| **Interface (UI)** | Streamlit | Prototipagem rápida e criação do "cockpit" DRC. |
| **Backend (API/Facade)** | FastAPI (Opcional) | Para lógica de negócios complexa ou *facade* de acesso ao FHIR. |
| **Cliente FHIR** | `fhirpy` ou `fhirclient` | Interação com o Servidor FHIR (CRUD e Search). |
| **Visualização** | Plotly/Altair | Geração dos gráficos de tendência (eGFR, PA, Albuminúria). |
| **Infraestrutura** | Docker | Empacotamento do ambiente para deploy fácil e consistente. |

## 3. Padrões de Codificação Python

Os desenvolvedores de IA devem aderir estritamente aos seguintes padrões:

### 3.1. PEP 8 e Formatação
Todo o código Python deve seguir o guia de estilo **PEP 8**.
*   **Formatação:** Usar `black` ou `ruff` para formatação automática.
*   **Docstrings:** Usar o formato **Google Style** para documentar funções e classes.

### 3.2. Tipagem Estática
O uso de **Type Hinting** (dicas de tipo) é obrigatório para todas as funções, métodos e variáveis. Isso aumenta a clareza do código e facilita a detecção de erros.

### 3.3. Modularidade e Testabilidade
*   **Separação de Responsabilidades:** O código deve ser dividido em módulos lógicos (ex: `fhir_client.py`, `drc_logic.py`, `ui_components.py`).
*   **Testes:** O código gerado deve ser **testável**. Evitar lógica complexa diretamente na UI (Streamlit); movê-la para funções puras em módulos separados.

## 4. Padrões FHIR e Interoperabilidade

### 4.1. Versão FHIR
O projeto utilizará a versão **FHIR R4** (Release 4).

### 4.2. Recursos Mínimos
O código deve manipular os seguintes recursos FHIR conforme definido no escopo:
*   `Patient` (Identificação)
*   `Observation` (PA, eGFR, K+, ACR, etc.)
*   `Condition` (DRC, DM, HAS)
*   `MedicationStatement` ou `MedicationRequest` (Medicações-chave)
*   `CarePlan` (Pendências e Metas)
*   `Goal` (Metas de tratamento)
*   `Provenance` (Rastreabilidade de quem registrou)

### 4.3. Nomenclatura e Codificação
*   **Códigos:** Sempre que possível, usar sistemas de codificação padrão (ex: **LOINC** para Observações, **SNOMED CT** para Condições).
*   **Extensões:** Evitar o uso de extensões FHIR, a menos que seja estritamente necessário para o protótipo.

## 5. Diretrizes para os Desenvolvedores IA (Claude/GPT)

Ao gerar código, os desenvolvedores de IA devem priorizar:

1.  **Código Limpo e Legível:** A clareza é mais importante do que a otimização prematura.
2.  **Uso de Funções e Classes:** Evitar scripts monolíticos. Usar classes para encapsular a lógica (ex: `DRCFHIRClient` para todas as operações FHIR).
3.  **Comentários:** Incluir comentários claros sobre a lógica de negócios e a razão de ser de cada componente.
4.  **Tratamento de Erros:** Implementar blocos `try...except` robustos, especialmente nas chamadas de API (FHIR).
5.  **Configuração:** Usar variáveis de ambiente ou um arquivo `.env` para credenciais e URLs de API (Servidor FHIR, Vertex AI). **NUNCA** codificar credenciais diretamente.

---
**Próximo Passo:** Iniciar a Modelagem FHIR dos *Profiles* de DRC e a criação do esqueleto do repositório.
