# Especificação Funcional de Modelagem FHIR - Painel DRC

**Documento:** 03_Especificacao_Funcional_FHIR
**Projeto:** Painel DRC (Protótipo)
**Versão:** 1.0
**Data:** 30 de Janeiro de 2026
**Elaboração:** Manus AI

Este documento detalha a **Modelagem FHIR** necessária para o protótipo do Painel DRC, servindo como a **Especificação Funcional** a ser utilizada pelo Desenvolvedor IA para a criação da Especificação Técnica e, posteriormente, do código.

O foco é o **Mínimo Produto Viável (MVP)**, conforme definido no escopo original, para garantir a entrega rápida e a validação do conceito.

## 1. Princípios de Modelagem

1.  **Versão FHIR:** Utilizar **FHIR R4**.
2.  **Recursos:** Focar nos recursos mínimos necessários para o "Resumo DRC" e a "Entrada de Dados" (Seções 3.1 e 3.2 do Escopo).
3.  **Codificação:** Priorizar o uso de sistemas de códigos padrão (LOINC, SNOMED CT) para garantir a interoperabilidade futura.

## 2. Recursos FHIR e Mapeamento de Dados

A tabela a seguir detalha os recursos FHIR essenciais e os elementos de dados correspondentes para o MVP.

| Recurso FHIR | Elemento de Dados (Escopo) | Uso no Painel | Notas de Modelagem |
| :--- | :--- | :--- | :--- |
| **Patient** | Identificação & Vínculo | Exibição do nome, CNS/CPF, unidade APS. | O recurso base é suficiente. |
| **Condition** | Status DRC (Estágio, Etiologia), Condições Associadas (DM, HAS) | Exibição do diagnóstico principal e comorbidades. | Usar `code` para DRC (SNOMED CT) e `stage` para o Estágio G1-G5. |
| **Observation** | eGFR, Creatinina, PA, Albuminúria (ACR/PCR), Potássio (K+) | Gráficos de Tendência e Status. | **Essencial:** Usar `code` LOINC para cada tipo de observação. `valueQuantity` para o valor e unidade. |
| **MedicationStatement** | Medicações-chave (iECA/BRA, iSGLT2, etc.) | Lista de medicamentos ativos. | Usar `medicationCodeableConcept` ou referência a `Medication`. |
| **CarePlan** | Pendências & Próximos Passos | Lista de tarefas e plano de cuidado compartilhado. | Usar `activity` para listar as pendências. |
| **Goal** | Metas (PA alvo, Albuminúria) | Exibição das metas de tratamento. | Usar `target` para definir o valor alvo e `description` para a meta. |
| **Provenance** | Rastreabilidade (Quem/Onde/Quando) | Registro de quem inseriu cada dado (APS ou AES). | **Obrigatório:** Deve ser gerado para cada `Observation`, `Condition` ou `MedicationStatement` criado/atualizado. |

## 3. Detalhamento de Observações (Observation)

O coração do painel são as observações longitudinais. O Desenvolvedor IA deve garantir que o cliente FHIR possa buscar e organizar esses dados para a plotagem dos gráficos.

| Observação | Código LOINC (Sugerido) | Unidade (Sugerida) | Notas |
| :--- | :--- | :--- | :--- |
| **eGFR** | `33914-3` (Estimated Glomerular Filtration Rate) | `mL/min/{1.73m2}` | Necessário para o gráfico de tendência principal. |
| **Creatinina** | `2160-0` (Creatinine [Mass/volume] in Serum or Plasma) | `mg/dL` ou `umol/L` | Pode ser usado para calcular o eGFR se não estiver disponível. |
| **Pressão Arterial (PA)** | `85354-9` (Blood pressure panel) | `mm[Hg]` | Deve ser modelado como um painel com componentes para Sistólica (`8480-6`) e Diastólica (`8462-4`). |
| **Relação Albumina/Creatinina (ACR)** | `14958-3` (Albumin/Creatinine ratio in Urine) | `mg/g` | Necessário para o gráfico de albuminúria. |
| **Potássio (K+)** | `2823-3` (Potassium [Moles/volume] in Serum or Plasma) | `mmol/L` | Essencial para segurança terapêutica. |

## 4. Lógica Funcional para o Painel

O Desenvolvedor IA deve considerar a seguinte lógica ao criar o cliente FHIR e a lógica de *core*:

### 4.1. Resumo DRC (Monograph View)
*   **Busca de Paciente:** O cliente FHIR deve suportar a busca de um paciente por ID ou identificador (ex: CNS/CPF).
*   **Busca Longitudinal:** Para os gráficos, o cliente deve realizar buscas do tipo `Observation?patient=[ID]&code=[LOINC]&_sort=date` para recuperar a série histórica.
*   **Status DRC:** O estágio G1-G5 e A1-A3 deve ser inferido a partir da `Condition` mais recente e da `Observation` de ACR/eGFR mais recente.

### 4.2. Entrada de Dados (Registro Rápido)
O cliente FHIR deve suportar as seguintes operações de criação (POST):
*   **Adicionar PA:** Criação de um recurso `Observation` (Painel PA).
*   **Adicionar Exame:** Criação de um ou mais recursos `Observation` (eGFR, ACR, K+).
*   **Adicionar Nota/Conduta:** Criação de um `CarePlan.note` ou `DocumentReference` simples.
*   **Criar Pendência:** Criação de um `CarePlan.activity` ou `Goal`.

### 4.3. Rastreabilidade (Provenance)
Toda operação de criação ou atualização de dados clínicos deve ser acompanhada da criação de um recurso `Provenance` que referencie o recurso modificado e o `Practitioner` (usuário) responsável.

## 5. Próximo Passo para o Desenvolvedor IA

Com base nesta Especificação Funcional, o Desenvolvedor IA deve:

1.  **Elaborar a Especificação Técnica:** Detalhar as classes Python necessárias (`DRCFHIRClient`, `DRCCoreLogic`), as funções de busca FHIR (com exemplos de *queries* REST) e a estrutura de dados interna (Pandas DataFrames ou Pydantic Models) para manipular os recursos FHIR.
2.  **Definir o Mock FHIR:** Propor a estrutura de um *dataset* sintético (JSON FHIR) que demonstre a longitudinalidade dos dados.

O resultado desta etapa será a **Especificação Técnica**, que será revisada pelo Arquiteto e pelo Planejador (Manus AI) antes da implementação.
