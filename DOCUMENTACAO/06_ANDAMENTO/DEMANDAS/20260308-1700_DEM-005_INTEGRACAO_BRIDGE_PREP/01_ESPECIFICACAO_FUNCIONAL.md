# DEM-005 — Portas de Integração HIS: Especificação Funcional

**Demanda:** DEM-005
**Módulo principal:** intellicare-core (+ intellicare-grahame · intellicare-wanda · intellicare-auth · intellicare-bridge)
**Dev:** dev3
**Branch:** `feature/bridge-integration-prep`
**Referência:** `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP.md`

---

## O que é

Esta demanda prepara o IntelliCare para receber dados de **Sistemas de Informação Hospitalar (HIS)** externos — como Philips Tasy, SOUL MV, TOTVS RM, Feegow e Pixeon — sem implementar nenhum adaptador real ainda.

O trabalho consiste em criar os **"encaixes"**: contratos, endpoints e estruturas que os adaptadores futuros vão usar para se conectar à plataforma. Quando chegar a hora de integrar com um HIS específico, o desenvolvedor terá tudo que precisa pronto — sem precisar refatorar o core.

---

## Problema que resolve

O IntelliCare já possui toda a infraestrutura clínica necessária (FHIR R4, SMART on FHIR, CDS Hooks, HL7v2). O que falta é a **porta de entrada padronizada** para que HIS externos possam enviar dados de pacientes para a plataforma de forma segura e estruturada.

Sem esta demanda, quando um cliente pedir integração com seu HIS (ex: Feegow), o desenvolvedor teria que inventar uma forma de entrada do zero — sem contrato definido, sem modelo de contexto, sem autenticação padronizada — gerando retrabalho e inconsistências.

---

## O que já existe na plataforma

A maior parte da integração já está implementada e funcionando:

| Componente | Onde está | Status |
|---|---|---|
| Servidor FHIR R4 (receptor de dados) | GRAHAME (porta 8012) | ✅ Funcionando |
| SMART on FHIR 2.0 (autenticação) | intellicare-auth | ✅ Funcionando |
| EHR Launch (iniciar sessão a partir do HIS) | GRAHAME `/smart/launch` | ✅ Funcionando |
| CDS Hooks 2.0 (alertas clínicos ao HIS) | GRAHAME `/cds-hooks/` | ✅ Funcionando |
| HL7v2 (ingestão de mensagens legadas) | GRAHAME `/fhir/hl7v2/` | ✅ Funcionando |
| Orquestrador multi-agente | WANDA (porta 8004) | ✅ Funcionando |

---

## O que esta demanda entrega

### 1. Contrato padronizado de contexto HIS (`HISContext`)

Sempre que um HIS envia dados para o IntelliCare, precisa informar de onde vem: qual sistema, qual paciente, qual atendimento, qual profissional. O `HISContext` é o modelo padrão para carregar essa informação entre os módulos.

Do ponto de vista do administrador da plataforma: quando um HIS envia um paciente, o IntelliCare sabe automaticamente que aquele dado veio do Feegow, vinculado ao tenant X, atendimento Y — sem ambiguidade.

### 2. Porta de entrada em batch para o GRAHAME

O GRAHAME já aceita recursos FHIR individualmente (um paciente por vez, uma observação por vez). Esta demanda adiciona um endpoint que aceita um **Bundle completo** — todos os dados de um atendimento de uma vez.

Do ponto de vista do administrador: ao integrar com um HIS, os dados chegam em bloco (paciente + diagnósticos + medicamentos + sinais vitais) em uma única operação — mais eficiente e atômico.

### 3. WANDA reconhece origem HIS

Quando o WANDA recebe uma análise de paciente que veio via integração HIS, ele propagará esse contexto para todos os agentes clínicos (OSWALDO, FLORENCE, DONABEDIAN), mantendo a rastreabilidade da origem.

Do ponto de vista do administrador: é possível saber, em qualquer análise, se ela foi disparada manualmente por um usuário do portal ou automaticamente por uma integração com o HIS.

### 4. Perfil de autenticação para adaptadores (`HIS_ADAPTER`)

Cada futuro adaptador HIS terá uma identidade própria no Keycloak — um "service account" com permissões específicas. Esta demanda cria o perfil base (`HIS_ADAPTER`) e um service account de teste (`intellicare-bridge-dev`).

Do ponto de vista do administrador: o acesso de cada HIS pode ser revogado individualmente. Um adaptador Feegow comprometido não dá acesso a nada além do que ele precisa.

### 5. Módulo stub `intellicare-bridge`

Um módulo de esqueleto, sem implementação real, que reserva a porta 8014 e define a estrutura de diretórios e arquivos que os adaptadores vão usar. Aparece nos dashboards de health como "em espera".

Do ponto de vista do administrador: ao abrir o painel de módulos (DEM-004), `intellicare-bridge` aparece com status "stub" — indicando que a infraestrutura está pronta mas nenhum HIS está conectado ainda.

---

## O que esta demanda NÃO faz

- Não implementa nenhum adaptador HIS real (Feegow, Tasy, MV, TOTVS, Pixeon)
- Não conecta com nenhum HIS externo
- Não importa dados reais de pacientes de nenhuma fonte externa
- Não altera o fluxo existente de usuários do portal
- Não modifica autenticação de usuários humanos (apenas cria perfil para service accounts HIS)
- Não implementa lógica de mapeamento de IDs entre HIS e IntelliCare

---

## Fluxo de uso típico (futuro — quando adaptadores estiverem implementados)

1. Médico abre prontuário no Feegow (HIS do hospital)
2. Feegow dispara um EHR Launch: `GET /smart/launch?launch=TOKEN&iss=FEEGOW_URL`
3. GRAHAME processa o launch e autentica o FeegoAdapter
4. FeegoAdapter (futuro) busca dados do paciente na API Feegow e converte para FHIR Bundle
5. FeegoAdapter envia o Bundle para `POST /api/v1/fhir/$process-message` no GRAHAME ← **novo**
6. GRAHAME processa cada recurso FHIR e publica evento no Redis
7. WANDA consome o evento, reconhece o `HISContext` ← **novo**, e inicia análise automática
8. OSWALDO analisa o paciente, DONABEDIAN calcula indicadores de qualidade
9. CDS Hooks retorna alertas para o Feegow exibir ao médico

**Esta demanda prepara os passos 5, 6 e 7.** Os passos 3 e 4 (FeegoAdapter) são demanda futura.

---

## HIS planejados e prioridade de implementação futura

| Prioridade | HIS | Tecnologia | Critério |
|---|---|---|---|
| 1º | **Feegow** | API REST v1.0, token estático | Mais simples, valida o fluxo end-to-end |
| 2º | TOTVS RM | API REST documentada | Portal TOTVS Developers bem documentado |
| 3º | SOUL MV | Plataforma de Interoperabilidade MV | Foco em FHIR, terceiro em complexidade |
| 4º | Philips Tasy | SOAP/REST híbrido | Alta penetração em hospitais públicos |
| 5º | Pixeon/SisHOSP | Barramento local | Implementar por demanda de cliente |
