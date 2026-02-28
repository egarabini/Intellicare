# EF-F002 — Persistencia de Analises Clinicas

> Ativar a persistencia de analises laboratoriais no PostgreSQL, criando historico automatico por paciente e habilitando o TrendDetector a usar historico proprio ao inves de depender do caller.

## 1. Objetivo

Transformar a Florence de motor stateless em sistema com memoria clinica:
- Cada analise e automaticamente salva no banco com o resultado completo
- TrendDetector consulta banco diretamente (sem precisar que o caller forneca historico)
- Historico de exames por paciente disponivel em endpoints dedicados
- Base para que Oswaldo possa consultar historico laboratorial da Florence (EF-F007)

## 2. Justificativa

- Hoje cada chamada a Florence e independente — nao ha aprendizado sobre o paciente
- TrendDetector e excelente mas requer que o chamador forneca series temporais — impratico clinicamente
- Sem historico, nao e possivel detectar progressao de IRC (creatinina subindo mes a mes)
- Models SQLAlchemy e migration Alembic ja existem — e necessario apenas ativar e integrar
- Oswaldo precisa do historico de HbA1c, creatinina e outros para seus estadiamentos

## 3. Escopo

### 3.1 Schema de Banco de Dados

```sql
-- Tabela principal: cada analise completa
CREATE TABLE florence_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(100) NOT NULL,        -- ID do paciente (anonimizado se LGPD)
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_by VARCHAR(100),               -- Agente ou usuario que solicitou
    capability_used VARCHAR(50),             -- "lab_interpretation" | "clinical_analysis" etc

    -- Resultado completo em JSON
    lab_results JSONB NOT NULL,              -- Input: {creatinine: 2.1, egfr: 38}
    interpretations JSONB,                   -- Output: interpretacao de cada exame
    patterns_detected JSONB,                 -- Output: padroes clinicos detectados
    summary TEXT,                            -- Resumo textual da analise

    -- Flags de significancia
    has_critical_values BOOLEAN DEFAULT FALSE,
    has_urgent_values BOOLEAN DEFAULT FALSE,
    overall_significance VARCHAR(20),        -- "normal" | "attention" | "urgent" | "critical"

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice por paciente + data (consultas frequentes)
CREATE INDEX idx_analyses_patient_date ON florence_analyses (patient_id, analyzed_at DESC);

-- Tabela de medicoes individuais (para TrendDetector)
CREATE TABLE florence_lab_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES florence_analyses(id) ON DELETE CASCADE,
    patient_id VARCHAR(100) NOT NULL,
    lab_id VARCHAR(50) NOT NULL,             -- "creatinine" | "egfr" | "hba1c" etc
    value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20),
    loinc_code VARCHAR(20),
    level VARCHAR(20),                       -- "normal" | "high" | "critical_high" etc
    significance VARCHAR(20),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indice para TrendDetector: paciente + lab_id + data
CREATE INDEX idx_measurements_patient_lab ON florence_lab_measurements (patient_id, lab_id, measured_at DESC);
```

### 3.2 AnalysisRepository

```python
class AnalysisRepository:
    """
    Repositorio para persistencia de analises da Florence.
    Usa asyncpg via SQLAlchemy async.
    """

    async def save_analysis(
        self,
        patient_id: str,
        lab_results: dict,
        analysis: ClinicalAnalysis,
        requested_by: Optional[str] = None,
        capability_used: Optional[str] = None,
    ) -> str:
        """
        Salva analise completa e medicoes individuais.
        Retorna: analysis_id (UUID)

        Executado automaticamente apos cada chamada ao ClinicalAnalyzer.
        """

    async def get_patient_analyses(
        self,
        patient_id: str,
        limit: int = 20,
        lab_id: Optional[str] = None,          # Filtrar por exame especifico
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[dict]:
        """
        Recupera analises de um paciente ordenadas por data desc.
        """

    async def get_lab_history(
        self,
        patient_id: str,
        lab_id: str,
        limit: int = 12,                        # Ultimas 12 medicoes (1 ano mensal)
        from_date: Optional[str] = None,
    ) -> list[dict]:
        """
        Serie temporal de um exame especifico.
        Formato: [{"measured_at": "...", "value": 2.1, "level": "high"}, ...]

        Usado pelo TrendDetector sem precisar de input externo.
        """

    async def get_latest_analysis(
        self,
        patient_id: str,
    ) -> Optional[dict]:
        """Retorna a analise mais recente do paciente."""

    async def delete_patient_data(
        self,
        patient_id: str,
    ) -> int:
        """
        Remove todos os dados de um paciente (direito ao esquecimento LGPD).
        Retorna: numero de registros removidos.
        """
```

### 3.3 Integracao no ClinicalAnalyzer

```python
class ClinicalAnalyzer:
    """
    Versao atualizada — salva automaticamente cada analise.
    """

    def __init__(self, config: FlorenceConfig, repository: AnalysisRepository):
        self._repo = repository
        # ... resto igual

    async def analyze_labs(
        self,
        patient_id: str,
        lab_results: dict,
        timestamp: Optional[str] = None,
        save: bool = True,                  # Persistir por padrao (False para testes)
    ) -> ClinicalAnalysis:
        """
        Analise + save automatico.

        1. Executa analise normal (comportamento existente)
        2. Se save=True e patient_id valido: salva no banco
        3. Retorna ClinicalAnalysis (comportamento identico ao atual)
        """

    async def analyze_with_trends(
        self,
        patient_id: str,
        lab_results: dict,
        historical: Optional[dict] = None,   # Ainda aceita historico externo
        timestamp: Optional[str] = None,
    ) -> ClinicalAnalysis:
        """
        Se historical=None: busca automaticamente do banco.
        Se historical fornecido: usa o fornecido (retro-compatibilidade).
        """
```

### 3.4 Endpoints REST Novos

```python
# GET /api/v1/patients/{patient_id}/analyses
# Query params: limit (default 20), lab_id, from_date, to_date
# Retorna: lista de analises do paciente

# GET /api/v1/patients/{patient_id}/labs/{lab_id}/history
# Query params: limit (default 12), from_date
# Retorna: serie temporal para TrendDetector

# GET /api/v1/patients/{patient_id}/analyses/latest
# Retorna: ultima analise do paciente

# DELETE /api/v1/patients/{patient_id}/data
# LGPD: remove todos os dados do paciente
# Retorna: {deleted_count: N, patient_id: "..."}
```

### 3.5 Migration Alembic

```python
# alembic/versions/002_florence_persistence.py
# Cria as tabelas florence_analyses e florence_lab_measurements
# A migration 001_initial_create_tables.py existente e para tabelas legacy (nao usar)

def upgrade() -> None:
    op.create_table(
        'florence_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), ...),
        # ... columns
    )
    op.create_table(
        'florence_lab_measurements',
        # ... columns
    )
    op.create_index(...)
```

### 3.6 Configuracao

```env
# Banco de dados (PostgreSQL)
FLORENCE_DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/florencedb
FLORENCE_DB_POOL_SIZE=5
FLORENCE_DB_MAX_OVERFLOW=10

# Retencao de dados (LGPD)
FLORENCE_DATA_RETENTION_DAYS=365          # Apagar analises > 1 ano automaticamente
FLORENCE_AUTO_SAVE_ANALYSES=true          # Salvar cada analise automaticamente
FLORENCE_SAVE_ANONYMIZED=true             # Salvar patient_id anonimizado (SHA256 + salt)
```

## 4. Testes

- AnalysisRepository.save_analysis: analise completa salva corretamente (2 testes)
- AnalysisRepository.get_lab_history: retorna serie temporal correta, paciente sem historico (2 testes)
- AnalysisRepository.delete_patient_data: remove tudo (1 teste)
- ClinicalAnalyzer.analyze_labs: save=True persiste, save=False nao persiste (2 testes)
- ClinicalAnalyzer.analyze_with_trends: sem historical busca do banco, com historical usa fornecido (2 testes)
- Endpoints: GET analyses, GET history, DELETE data (4 testes)
- Migracao: tabelas criadas corretamente (1 teste)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] `florence_analyses` e `florence_lab_measurements` criadas com migration Alembic
- [ ] `ClinicalAnalyzer.analyze_labs` salva automaticamente apos cada analise
- [ ] `analyze_with_trends` busca historico do banco se nao fornecido externamente
- [ ] `DELETE /api/v1/patients/{id}/data` remove todos os dados (LGPD)
- [ ] Endpoint de historico de exames por lab_id (para TrendDetector)
- [ ] Configuracao por ENV: FLORENCE_AUTO_SAVE_ANALYSES
- [ ] 198 testes existentes continuam passando
- [ ] 15+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/db/repository.py`, `florence/db/__init__.py`, `alembic/versions/002_florence_persistence.py`
- **Arquivos modificados**: `florence/engine/clinical_analyzer.py` (integrar repo), `florence/api/app.py` (4 novos endpoints), `florence/config.py`
- **Linhas estimadas**: ~350
- **Testes novos**: ~15
