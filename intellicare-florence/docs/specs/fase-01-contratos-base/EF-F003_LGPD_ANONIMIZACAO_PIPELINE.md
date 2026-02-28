# EF-F003 — LGPD e Anonimizacao no Pipeline

> Ativar o modulo de anonimizacao existente no pipeline da Florence, garantindo que dados de pacientes sejam tratados conforme a LGPD antes de qualquer persistencia ou log.

## 1. Objetivo

O modulo de anonimizacao foi criado (17 testes passando), mas nao esta integrado ao pipeline de analise. Esta spec ativa e integra:
- Pseudonimizacao de `patient_id` (SHA256 + salt) antes de salvar no banco
- Remocao de dados diretamente identificaveis de logs
- Endpoint de esquecimento (direito LGPD Art. 18)
- Audit log de quem acessou dados de qual paciente

## 2. Justificativa

- LGPD (Lei 13.709/2018): dados de saude sao dados sensiveis — protecao obrigatoria
- ANS e CFM exigem tratamento adequado de dados clinicos
- Sem anonimizacao, `patient_id` real aparece em logs, banco e ChromaDB
- O modulo de anonimizacao ja existe e tem 17 testes — apenas precisa ser ativado
- Preparatorio para certificacao ISO 27001 e SOC 2

## 3. Escopo

### 3.1 O Que Ja Existe (NAO REIMPLEMENTAR)

O modulo `test_anonymization.py` testa 17 casos — o modulo existe. Verificar:
- `florence/anonymization/` ou `florence/security/` — onde esta o modulo
- Funcionalidades ja testadas: pseudonimizacao de IDs, remocao de CPF, anonimizacao de nomes

### 3.2 AnonymizationPipeline (Integracao)

```python
class AnonymizationPipeline:
    """
    Integra anonimizacao ao pipeline da Florence.
    Instanciado uma vez na startup e injetado onde necessario.

    Principios LGPD aplicados:
    - Pseudonimizacao: patient_id → hash_id (SHA256 + salt secreto)
    - Minimizacao: apenas dados necessarios sao persistidos
    - Finalidade: dados usados apenas para o fim declarado (analise clinica)
    - Direito ao esquecimento: DELETE em todos os registros do paciente

    O salt DEVE ser diferente por ambiente (dev/staging/prod).
    Sem o salt, nao e possivel reverter o hash — intencional.
    """

    def pseudonymize_patient_id(self, patient_id: str) -> str:
        """
        SHA256(patient_id + FLORENCE_LGPD_SALT)
        Deterministico: mesmo patient_id sempre gera mesmo hash.
        Permite consultar historico do paciente sem expor ID real.

        Ex: "12345" → "a3f8c2..." (64 chars hex)
        """

    def clean_for_log(self, data: dict) -> dict:
        """
        Remove ou mascara campos sensiveis antes de logar.

        Campos que NUNCA aparecem em log:
        - patient_id (ou qualquer ID de pessoa)
        - lab_results (valores numericos ficam, mas sem contexto pessoal)
        - nome, cpf, data_nascimento se presentes no context

        Ex: {"patient_id": "123", "lab_results": {...}} →
            {"patient_id": "[REDACTED]", "lab_results_count": 4}
        """

    def validate_consent(
        self,
        patient_id: str,
        purpose: str,
    ) -> bool:
        """
        Verifica se ha consentimento registrado para o fim declarado.
        Integra com o futuro modulo de consentimento (FASE FUTURA).
        Por ora: retorna True se FLORENCE_LGPD_REQUIRE_CONSENT=false (default dev).
        """
```

### 3.3 Pontos de Integracao no Pipeline

```python
# 1. ClinicalAnalyzer.analyze_labs — antes de persistir
async def analyze_labs(self, patient_id: str, lab_results: dict, ...):
    # Analise normal (sem mudar)
    analysis = await self._do_analysis(lab_results)

    if self._config.auto_save and patient_id:
        # LGPD: pseudonimizar antes de salvar
        safe_patient_id = self._anonymizer.pseudonymize_patient_id(patient_id)
        await self._repo.save_analysis(patient_id=safe_patient_id, ...)

    return analysis  # Retorna ao caller com patient_id original


# 2. Logs — remover dados sensiveis
import logging
logger = logging.getLogger("florence")

# ERRADO (antes):
# logger.info(f"Analisando paciente {patient_id}, labs: {lab_results}")

# CORRETO (depois — via clean_for_log):
# logger.info(f"Analise iniciada: {anonymizer.clean_for_log({'patient_id': patient_id, ...})}")


# 3. ChromaDB RAG — queries nao devem conter patient_id
# RAG queries sao baseadas em achados clinicos, nunca em ID de paciente
# Isso ja e correto na implementacao atual — apenas documentar e validar em teste
```

### 3.4 Audit Log

```python
class FlorenceAuditLog:
    """
    Registra acessos a dados de pacientes.
    Obrigatorio pela LGPD para dados sensiveis.

    Salvo em tabela separada (nao no log de aplicacao).
    """

    async def log_access(
        self,
        pseudonymized_patient_id: str,   # Hash, nunca o ID real
        requester: str,                   # "wanda" | "oswaldo" | "user:abc" | "api:key123"
        capability: str,                  # "clinical_analysis"
        data_accessed: list[str],         # ["creatinine", "egfr"] — quais dados foram lidos
        purpose: str,                     # "clinical_analysis" | "trend_detection"
    ) -> None:
        """Registra acesso para auditoria LGPD."""
```

```sql
-- Nova tabela de audit
CREATE TABLE florence_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pseudonymized_patient_id VARCHAR(64) NOT NULL,  -- SHA256 hash
    requester VARCHAR(100) NOT NULL,
    capability VARCHAR(50),
    data_accessed JSONB,
    purpose VARCHAR(100),
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Particionar por mes para facilitar retencao (LGPD: guardar audit por 5 anos)
CREATE INDEX idx_audit_patient ON florence_audit_log (pseudonymized_patient_id, accessed_at DESC);
```

### 3.5 Endpoints LGPD

```python
# DELETE /api/v1/lgpd/patients/{patient_id}/data
# Direito ao esquecimento (Art. 18, VI LGPD)
# Remove: florence_analyses + florence_lab_measurements
# Retorna: {deleted_analyses: N, deleted_measurements: M, patient_id: "[REDACTED]"}
# NOTA: o patient_id recebido e pseudonimizado internamente antes da busca

# GET /api/v1/lgpd/patients/{patient_id}/data-export
# Direito de acesso (Art. 18, I LGPD)
# Exporta todos os dados do paciente em JSON
# Retorna: {analyses: [...], measurements: [...], period: "..."}

# GET /api/v1/lgpd/info
# Informacoes sobre tratamento de dados
# Retorna: {controller, purpose, retention_days, contact, basis}
```

### 3.6 Configuracao

```env
# LGPD
FLORENCE_LGPD_SALT=<secret-random-value>          # OBRIGATORIO em producao
FLORENCE_LGPD_REQUIRE_CONSENT=false               # true em producao
FLORENCE_LGPD_AUDIT_ENABLED=true
FLORENCE_DATA_RETENTION_DAYS=365                   # Apagar analises > 1 ano
FLORENCE_LGPD_CONTROLLER="IntelliCare Sistemas"   # Responsavel pelo tratamento
FLORENCE_LGPD_CONTACT="privacidade@intellicare.com"
```

## 4. Testes

- AnonymizationPipeline.pseudonymize_patient_id: deterministico, diferentes IDs geram hashes diferentes (2 testes)
- clean_for_log: patient_id redacted, lab_results sem contexto pessoal (2 testes)
- Integracao: analyze_labs salva com hash, nao com ID original (2 testes)
- Audit log: acesso registrado, campos corretos (2 testes)
- DELETE endpoint: remove dados, retorna contagem (1 teste)
- GET export: retorna todos os dados do paciente (1 teste)
- **Total**: 10+ testes novos

## 5. Criterios de Aceitacao

- [ ] `patient_id` nunca aparece em logs de aplicacao (logs testados)
- [ ] Banco de dados armazena apenas hash do patient_id (SHA256 + salt)
- [ ] `DELETE /api/v1/lgpd/patients/{id}/data` remove todos os dados
- [ ] `GET /api/v1/lgpd/patients/{id}/data-export` exporta dados para portabilidade
- [ ] Audit log registra todos os acessos a dados de pacientes
- [ ] FLORENCE_LGPD_SALT configuravel e obrigatorio em producao
- [ ] 198 testes existentes continuam passando (incluindo os 17 de anonimizacao)
- [ ] 10+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/lgpd/pipeline.py`, `florence/lgpd/audit.py`, `alembic/versions/003_florence_audit.py`
- **Arquivos modificados**: `florence/engine/clinical_analyzer.py` (integrar pipeline), `florence/api/app.py` (3 endpoints LGPD), `florence/config.py`
- **Linhas estimadas**: ~250
- **Testes novos**: ~10
