# W8-B — HL7v2 Agent — Especificação Funcional

**Workstream:** W8-B
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (+ novo sub-módulo `hl7v2`)
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Implementar agente HL7v2 mínimo para receber mensagens **ADT (Admit/Discharge/Transfer)** de sistemas legados brasileiros e converter para recursos FHIR R4, permitindo integração com sistemas hospitalares que não suportam FHIR.

---

## 2. Contexto de Negócio

### Problema Atual
Sistemas hospitalares brasileiros (PV, TASY, MV, SYSIMAL, etc.) usam protocolo **HL7v2** para troca de dados de admissão, alta e transferência de pacientes. O IntelliCare **não fala HL7v2**, exigindo adaptadores costosos.

### Solução Proposta
Endpoint que aceita mensagens HL7v2, faz parsing, converte para FHIR e dispara eventos internos (subscriptions). Sistema legado envia ADT → IntelliCare converte → FHIR disponível para outros módulos.

### Benefícios
- **Integração universal** com sistemas hospitalares brasileiros
- **Padrão internacional** (HL7v2 usado globalmente)
- **Baixa latência** (mensagens em tempo real)
- **Padrão ANS** (HL7v2 é requisito de certificação)

---

## 3. Requisitos Funcionais

### RF-001 — Receber Mensagens HL7v2
O sistema deve aceitar mensagens HL7v2:
- **Endpoint:** `POST /hl7v2/{message_type}`
- **Mensagem:** String HL7v2 (pipe-delimited)
- **Encoding:** ASCII, UTF-8, ISO-8859-1
- **Versões HL7:** 2.5, 2.5.1, 2.6 (compatibilidade reversa)

### RF-002 — Parsing HL7v2 (MVP)
O parser deve extrair informações de mensagens **ADT^A04** (register patient):
- **MSH segment:** Message header, timestamp, message type
- **PID segment:** Patient ID, name, birthdate, gender, race, address, phone
- **PV1 segment:** Visit number, patient class, location, admission type

### RF-003 — Validação HL7v2
O sistema deve validar:
- Estrutura de segmentos MSH, PID, PV1
- Campos obrigatórios por tipo de mensagem
- Checksum (MSH-12)
- Comprimento de campos

### RF-004 — Conversão para FHIR
O sistema deve converter ADT para recursos FHIR:
- **Patient:** dados demográficos (PID)
- **Encounter:** visita/atendimento (PV1)

### RF-005 — Geração de ACK
O sistema deve retornar ACK HL7v2:
- **ACK^A04** (application accept) para sucesso
- **ACK^AE** (application error) para erro
- Campos MSH-5, MSH-6 preenchidos corretamente

### RF-006 — Disparar Eventos Internos
O sistema deve disparar eventos FHIR:
- **Patient create** → triggers subscriptions FHIR
- **Encounter create** → triggers subscriptions FHIR
- **Publicação Redis Stream** → para WANDA/Geralda consumirem

### RF-007 — Autenticação
O endpoint deve ser protegido:
- **API Key** header (X-API-Key)
- **IP Whitelist** (configurável por tenant)
- **Mutual TLS** (opcional)

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- Latência de processamento: < 100ms (p99)
- Throughput: 100 mensagens/segundo
- Uso de memória: < 100MB por worker

### RNF-002 — Confiabilidade
- Taxa de sucesso parsing: ≥ 99%
- Zero message loss (fila persistida)
- Retry automático com backoff
- Dead letter queue para mensagens não processáveis

### RNF-003 — Segurança
- Validação de conteúdo malicioso
- Autenticação por API Key ou mTLS
- Autorização por tenant (cada hospital tem chave)
- Auditoria completa (log de todas as mensagens)

### RNF-004 — Compatibilidade
- Suporte a variações de hospitais (PV, TASY, MV)
- Suporte a encoding custom (ISO-8859-1, Windows-1252)
- Configuração flexível de mapeamento (HL7 → FHIR)

---

## 5. Interfaces

### 5.1 Endpoint Principal

```
POST /hl7v2/adt-a04
Content-Type: application/x-hl7-v2
X-API-Key: sk_test_xxxxx

MSH|^~\&|INTEGRICARE|GRAHAME|20260224100000||ADT^A04|MSG00001|P|2.5|||ER|AL||UNICODE
PID|1||12345678900^TESTE^PATIENTE^^^^||19800101|M|||Rua Teste, 123^^São Paulo^SP^^BR||5511999999999|PT|BR
PV1|1|I|2000^01^Hospital Central^^^^BR|||||||||||||||||||||||||||||||||||
```

**Resposta 200 (ACK):**
```
MSH|^~\&|GRAHAME|INTEGRICARE|20260224100001||ACK^A04|MSG00001|P|2.5|||AL||UNICODE
MSA|AA|MSG00001
```

**Resposta 400 (erro):**
```
MSH|^~\&|GRAHAME|INTEGRICARE|20260224100001||ACK^AE|MSG00001|P|2.5|||AL||UNICODE
MSA|AE|MSG00001
ERR|||Required segment PID missing
```

### 5.2 Endpoint de Batch

```
POST /hl7v2/batch
Content-Type: application/x-hl7-v2-batch

MSH|^~\&|HOSPITAL|GRAHAME|20260224100000||ADT^A04|MSG00001|P|2.5
...

MSH|^~\&|HOSPITAL|GRAHAME|20260224100001||ADT^A04|MSG00002|P|2.5
...
```

**Resposta 207:** Lista de ACKs

---

## 6. Mapeamento HL7v2 → FHIR

### ADT^A04 (Register Patient)

| HL7v2 Segment | Campo | FHIR Resource | Campo FHIR |
|----------------|-------|---------------|-----------|
| **MSH** | MSH-4 (sending app) | — | Meta (source) |
| **MSH** | MSH-7 (datetime) | Encounter | `period.start` |
| **MSH** | MSH-10 (message control ID) | Encounter | `identifier[0]` |
| **PID** | PID-3 (patient ID list) | Patient | `identifier` |
| **PID** | PID-5 (patient name) | Patient | `name` |
| **PID** | PID-7 (datetime of birth) | Patient | `birthDate` |
| **PID** | PID-8 (admin sex) | Patient | `gender` |
| **PID** | PID-10 (race) | Patient | `extension[race]` |
| **PID** | PID-11 (address) | Patient | `address` |
| **PID** | PID-13 (phone) | Patient | `telecom` |
| **PID** | PID-22 (ethnicity) | Patient | `extension[ethnicity]` |
| **PV1** | PV1-1 (set ID) | Encounter | `identifier[1]` |
| **PV1** | PV1-2 (patient class) | Encounter | `class` |
| **PV1** | PV1-3 (assigned location) | Encounter | `location[0]` |
| **PV1** | PV1-4 (admission type) | Encounter | `hospitalization.admitSource` |
| **PV1** | PV1-44 (admit datetime) | Encounter | `period.start` |

---

## 7. Casos de Uso

### UC-001 — Admissão de Paciente
**Ator:** Sistema Hospitalar (PV, TASY, MV)
**Fluxo:**
1. Hospital envia ADT^A04 via `POST /hl7v2/adt-a04`
2. Sistema valida mensagem HL7v2
3. Sistema converte para Patient + Encounter FHIR
4. Sistema persiste recursos FHIR
5. Sistema retorna ACK^A04
6. Sistema dispara evento FHIR (Patient/Encounter create)
7. Subscriptions FHIR processam evento (notificar Geralda, etc.)

### UC-002 — Alta de Paciente (Futuro)
**Ator:** Sistema Hospitalar
**Fluxo:**
1. Hospital envia ADT^A03 via `POST /hl7v2/adt-a03`
2. Sistema converte + atualiza Encounter (discharge)
3. Sistema dispara evento FHIR

### UC-003 — Erro de Parsing
**Ator:** Sistema Hospitalar
**Fluxo:**
1. Hospital envia ADT^A04 inválido
2. Sistema retorna ACK^AE com detalhes do erro
3. Sistema loga erro com detalhes
4. Mensagem original salva para análise

---

## 8. Critérios de Aceite

### CA-001 — Parsing HL7v2
- [x] Mensagem ADT^A04 válida é parseada
- [x] Todos os campos MSH, PID, PV1 são extraídos
- [x] Erros de estrutura retornam ACK^AE

### CA-002 — Conversão FHIR
- [x] ADT^A04 → FHIR Patient funciona
- [x] ADT^A04 → FHIR Encounter funciona
- [x] Campos obrigatórios mapeados corretamente

### CA-003 — ACK HL7v2
- [x] Sucesso retorna ACK^A04 (MSA|AA)
- [x] Erro retorna ACK^AE (MSA|AE)
- [x] MSH-5, MSH-6 preenchidos

### CA-004 — Eventos FHIR
- [x] Patient create dispara subscriptions
- [x] Encounter create dispara subscriptions
- [x] Redis Stream publicado

### CA-005 — Performance
- [x] Latência < 100ms (p99)
- [x] Throughput ≥ 100 msg/s
- [x] Memória < 100MB por worker

### CA-006 — Segurança
- [x] API Key obrigatório
- [x] IP whitelist funciona
- [x] Auditoria loga tudo

### CA-007 — Testes
- [x] 30+ testes com mensagens reais
- [x] Cobertura ≥ 80% do parser
- [x] Testes de carga passam (100 msg/s)

---

## 9. Escopo MVP vs Futuro

### MVP (Esta Onda)
- ADT^A04 (register patient)
- Endpoint `POST /hl7v2/adt-a04`
- Autenticação API Key
- Conversão Patient + Encounter
- Disparo de eventos FHIR

### Fase 2 (Futura)
- ADT^A03 (discharge patient)
- ADT^A08 (update patient info)
- ORM^O01 (order)
- ORU^R01 (observation result)
- ACK/NACK com detalhes
- Batch endpoint

---

## 10. Referências

### Especificações HL7v2
- **HL7 2.5:** https://hl7.org/documentcenter/publictemp/27B5F2E3-28C1-4E55-AAB3-3F8EB37C4A6D/HL7v2.5_2007.pdf
- **HL7 ADT Messages:** Chapter 3 (ADT)
- **ANS/DT:** Padrão brasileiro

### Código Medplum
- `packages/hl7/` — HL7v2 client/server TypeScript
- `packages/hl7/src/parse.ts` — Core parser
- `packages/hl7/src/segments/` — Segment parsers

### Documentação
- Medplum HL7: https://www.medplum.com/docs/hl7/
- HL7 Brasil: http://www.hl7brasil.org.br/
