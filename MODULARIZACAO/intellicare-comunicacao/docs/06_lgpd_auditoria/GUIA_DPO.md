# Guia Operacional para DPO (Data Protection Officer)

## 📋 Visão Geral

Este guia fornece instruções operacionais para o **Encarregado de Proteção de Dados (DPO)** do IntelliCare gerenciar conformidade LGPD no módulo de comunicação.

---

## 👤 Responsabilidades do DPO

Conforme Art. 41 da LGPD, o DPO deve:

1. ✅ **Aceitar reclamações** e comunicações dos titulares
2. ✅ **Prestar esclarecimentos** sobre tratamento de dados
3. ✅ **Receber comunicações** da ANPD (Autoridade Nacional)
4. ✅ **Orientar funcionários** sobre práticas de proteção de dados
5. ✅ **Executar demais atribuições** determinadas pelo controlador

---

## 🔐 Acesso ao Sistema

### Credenciais e Permissões

**Role Keycloak**: `data_protection_officer`

**Permissões**:
- ✅ Leitura completa de audit trail
- ✅ Exportação de dados de pacientes
- ✅ Anonimização de dados
- ✅ Verificação de integridade da hash chain
- ✅ Relatórios de conformidade

**Login**:
```bash
# URL: https://keycloak.gsi.srv.br/realms/bemcuidar
# Realm: bemcuidar
# Role: data_protection_officer
```

---

## 📊 Tarefas Diárias

### 1. Monitorar Audit Trail

**Objetivo**: Verificar se todas as comunicações estão sendo logadas corretamente.

**Endpoint**:
```bash
GET /api/v1/lgpd/audit?limit=100&offset=0
```

**Verificar**:
- ✅ Todas as comunicações têm `legal_basis` definida
- ✅ Overrides CRITICAL/HIGH estão justificados
- ✅ Não há comunicações bloqueadas indevidamente

**Exemplo**:
```bash
curl -X GET "https://comunicacao.gsi.srv.br/api/v1/lgpd/audit?limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2. Verificar Integridade da Hash Chain

**Objetivo**: Garantir que audit trail não foi adulterado.

**Endpoint**:
```bash
GET /api/v1/lgpd/verify-chain
```

**Resposta Esperada**:
```json
{
  "valid": true,
  "total_entries": 15234,
  "verified_entries": 15234,
  "broken_chains": []
}
```

**Ação se `valid: false`**:
1. 🚨 **ALERTA CRÍTICO**: Possível adulteração de dados
2. 📞 **Notificar**: Controlador de dados e equipe de segurança
3. 📝 **Documentar**: Incidente de segurança
4. 🔍 **Investigar**: Logs de acesso ao banco de dados

---

### 3. Relatório de Conformidade

**Objetivo**: Gerar relatório diário de conformidade LGPD.

**Endpoint**:
```bash
GET /api/v1/lgpd/compliance-report?start_date=2026-02-01&end_date=2026-02-18
```

**Resposta**:
```json
{
  "period": {
    "start": "2026-02-01",
    "end": "2026-02-18"
  },
  "total_communications": 5432,
  "by_legal_basis": {
    "consent": 3210,
    "vital_protection": 123,
    "health_protection": 456,
    "legal_obligation": 543,
    "public_interest": 1100
  },
  "blocked_communications": 234,
  "overrides_applied": 579,
  "consent_rate": 0.59
}
```

**Análise**:
- ✅ **consent_rate > 0.5**: Boa taxa de consentimento
- ⚠️ **overrides_applied alto**: Revisar se overrides estão justificados
- 🚨 **blocked_communications alto**: Investigar motivos de bloqueio

---

## 🙋 Atendimento a Solicitações de Titulares

### Solicitação 1: Acesso aos Dados (Art. 18, II)

**Requisição do Titular**:
> "Gostaria de saber quais dados vocês têm sobre mim."

**Procedimento**:

1. **Validar identidade** do titular (CPF, documento com foto)
2. **Exportar dados**:
```bash
GET /api/v1/lgpd/export/{patient_id}?format=json
```

3. **Enviar ao titular** em formato legível (JSON ou PDF)

**Prazo**: 15 dias (Art. 18, § 3º)

---

### Solicitação 2: Correção de Dados (Art. 18, III)

**Requisição do Titular**:
> "Meu telefone está errado no sistema."

**Procedimento**:

1. **Validar identidade** do titular
2. **Atualizar preferências**:
```bash
PUT /api/v1/lgpd/preferences/{patient_id}
Content-Type: application/json

{
  "phone": "+55 11 98765-4321"
}
```

3. **Confirmar** atualização ao titular

**Prazo**: Imediato

---

### Solicitação 3: Eliminação de Dados (Art. 18, VI)

**Requisição do Titular**:
> "Quero que meus dados sejam deletados."

**Procedimento**:

1. **Validar identidade** do titular
2. **Verificar obrigações legais**:
   - ⚠️ **Audit trail**: Deve ser mantido por 5 anos (requisito legal)
   - ✅ **Preferências**: Podem ser eliminadas

3. **Anonimizar dados**:
```bash
POST /api/v1/lgpd/anonymize/{patient_id}
```

4. **Confirmar** ao titular que:
   - ✅ Preferências foram eliminadas
   - ✅ Audit trail foi pseudonimizado (não reversível)
   - ⚠️ Dados clínicos em outros módulos (Florence, Prontuário) seguem retenção legal

**Prazo**: 15 dias

---

### Solicitação 4: Revogação de Consentimento (Art. 18, IX)

**Requisição do Titular**:
> "Não quero mais receber comunicações."

**Procedimento**:

1. **Validar identidade** do titular
2. **Revogar consentimento**:
```bash
DELETE /api/v1/lgpd/consent/{patient_id}
```

3. **Confirmar** ao titular que:
   - ✅ Consentimento foi revogado
   - ✅ Não receberá mais comunicações MEDIUM/LOW
   - ⚠️ Alertas CRITICAL/HIGH continuarão (proteção da vida)

**Prazo**: Imediato

---

## 📈 Relatórios Mensais para ANPD

### Relatório de Incidentes de Segurança

**Quando reportar**:
- 🚨 Vazamento de dados
- 🚨 Acesso não autorizado
- 🚨 Quebra de hash chain
- 🚨 Falha em sistemas de segurança

**Prazo**: 2 dias úteis após conhecimento do incidente (Art. 48)

**Template**:
```
RELATÓRIO DE INCIDENTE DE SEGURANÇA

Data do Incidente: [DATA]
Data de Conhecimento: [DATA]
Tipo de Incidente: [VAZAMENTO/ACESSO NÃO AUTORIZADO/OUTRO]

Dados Afetados:
- Número de titulares: [N]
- Tipos de dados: [PREFERÊNCIAS/AUDIT TRAIL/CONSENTIMENTO]
- Gravidade: [BAIXA/MÉDIA/ALTA]

Medidas Tomadas:
1. [AÇÃO 1]
2. [AÇÃO 2]

Medidas Preventivas:
1. [AÇÃO 1]
2. [AÇÃO 2]

DPO: [NOME]
Assinatura: [ASSINATURA DIGITAL]
```

---

## 🔍 Auditoria Interna

### Checklist Mensal

- [ ] Verificar integridade da hash chain
- [ ] Revisar overrides CRITICAL/HIGH (amostra de 10%)
- [ ] Verificar taxa de consentimento (target: > 50%)
- [ ] Revisar comunicações bloqueadas (investigar motivos)
- [ ] Verificar expiração de consentimentos (renovar se necessário)
- [ ] Testar endpoints de exportação de dados
- [ ] Revisar logs de acesso ao audit trail
- [ ] Verificar backups de audit trail (retenção de 5 anos)

---

## 📞 Contatos de Emergência

**Controlador de Dados**:
- Nome: [NOME DO CONTROLADOR]
- Email: controlador@intellicare.com.br
- Telefone: +55 11 1234-5678

**Equipe de Segurança**:
- Email: security@intellicare.com.br
- Telefone: +55 11 8765-4321

**ANPD**:
- Site: https://www.gov.br/anpd
- Email: atendimento@anpd.gov.br
- Telefone: 0800 000 0000

---

## 📚 Documentação de Referência

- **LGPD**: Lei nº 13.709/2018
- **Conformidade Legal**: `docs/06_lgpd_auditoria/CONFORMIDADE_LEGAL.md`
- **Integração D1**: `docs/06_lgpd_auditoria/INTEGRACAO_D1.md`
- **API Endpoints**: `docs/06_lgpd_auditoria/API.md`

