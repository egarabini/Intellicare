# EF-D003 — Importacao em Lote (CSV/JSON)

> Implementar upload de medicoes em lote via CSV e JSON, permitindo que hospitais importem dados exportados de seus sistemas de informacao (HIS, BI, planilhas).

## 1. Objetivo

Permitir carga em lote de medicoes de indicadores, eliminando a necessidade de entrada manual registro por registro:

- Upload de arquivo CSV com medicoes de um ou varios indicadores
- Upload de arquivo JSON com medicoes em formato estruturado
- Validacao em lote com relatorio de erros (sem "falhar silenciosamente")
- Importacao incremental (nao duplica registros existentes para o mesmo periodo)

## 2. Justificativa

- Hospitais tem dados em planilhas Excel, sistemas BI, ou HIS legados
- Entrada manual e impraticavel para carga historica (12-36 meses retroativos)
- Sem importacao em lote, adocao do modulo e limitada a novos dados
- CSV e o formato universal de exportacao de todos os HIS do mercado

## 3. Escopo

### 3.1 Formato CSV Padronizado

```csv
# Template: donabedian_medicoes_template.csv
# Codificacao: UTF-8, separador: ponto-e-virgula (;)
# Data: YYYY-MM-DD

indicator_id;indicator_name;period_start;period_end;period_type;value;unit;notes
550e8400-e29b-41d4-a716-446655440001;Taxa de infeccao hospitalar;2025-01-01;2025-01-31;monthly;2.1;%;Dado coletado pelo SCIH
550e8400-e29b-41d4-a716-446655440001;Taxa de infeccao hospitalar;2025-02-01;2025-02-28;monthly;1.9;%;Reducao apos protocolo
550e8400-e29b-41d4-a716-446655440002;Tempo medio permanencia;2025-01-01;2025-01-31;monthly;6.8;days;
```

**Campos obrigatorios**: `indicator_id` OU `indicator_name` (ao menos um), `period_start`, `period_end`, `value`
**Campos opcionais**: `period_type` (default: monthly), `unit`, `notes`

### 3.2 Formato JSON Padronizado

```json
{
    "import_metadata": {
        "source": "HIS-Philips-Tasy",
        "exported_at": "2026-02-16T10:00:00Z",
        "period": "2025",
        "hospital": "Hospital das Clinicas SP"
    },
    "measurements": [
        {
            "indicator_id": "550e8400-e29b-41d4-a716-446655440001",
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "period_type": "monthly",
            "value": 2.1,
            "unit": "%",
            "notes": "Dado SCIH"
        }
    ]
}
```

### 3.3 BulkImportService

```python
class BulkImportService:
    """
    Servico de importacao em lote de medicoes.

    Estrategia:
    1. Parsear arquivo (CSV ou JSON)
    2. Validar schema de cada linha/objeto
    3. Resolver indicator_name → indicator_id (se necessario)
    4. Verificar duplicatas (mesmo indicator + periodo ja existe)
    5. Calcular status automatico (verde/amarelo/vermelho) por medicao
    6. Salvar em lote com transaction (tudo ou nada por arquivo)
    7. Retornar relatorio detalhado (sucesso, erros, duplicatas ignoradas)

    Limite: 10.000 linhas por arquivo (reject se exceder).
    """

    MAX_ROWS_PER_FILE = 10_000

    async def import_csv(
        self,
        file_content: bytes,
        imported_by: str,
    ) -> BulkImportResult:
        """
        Importa medicoes de um arquivo CSV.

        Suporte a separadores: ';' e ','
        Suporte a encodings: UTF-8, ISO-8859-1, Windows-1252
        """

    async def import_json(
        self,
        file_content: bytes,
        imported_by: str,
    ) -> BulkImportResult:
        """
        Importa medicoes de um arquivo JSON.
        """

    async def validate_row(
        self,
        row: dict,
        indicators_cache: dict,    # Cache de indicadores do banco
    ) -> Optional[str]:
        """
        Valida uma linha de importacao.
        Retorna None se valido, ou mensagem de erro se invalido.

        Validacoes:
        - indicator_id existe no banco (ou indicator_name resolve)
        - period_start < period_end
        - value e numerico
        - period_type e enum valido
        """

    async def check_duplicates(
        self,
        rows: list[dict],
    ) -> list[dict]:
        """
        Identifica duplicatas (indicator + periodo ja existe).
        Duplicatas sao ignoradas (nao sobrescritas) por padrao.
        Retorna lista de rows duplicados para relatorio.
        """


@dataclass
class BulkImportResult:
    """
    Resultado de uma importacao em lote.
    """
    import_id: str               # UUID para rastrear a importacao
    file_name: str
    file_format: str             # "csv" ou "json"

    total_rows: int
    success_count: int
    error_count: int
    duplicate_count: int         # Ignorados (ja existiam)

    # Detalhes
    errors: list[dict]           # [{row: 5, field: "value", error: "nao numerico"}]
    duplicates: list[dict]       # [{indicator, period, action: "ignorado"}]

    # Status
    status: str                  # "success", "partial", "failed"
    imported_at: str

    # Acoes
    can_retry: bool              # True se erros sao corrigiveis
    error_file_url: Optional[str]  # CSV de erros para download
```

### 3.4 Endpoints REST Novos

```python
# POST /api/v1/measurements/import/csv
# Content-Type: multipart/form-data
# Body: file (CSV), encoding (opcional, default auto-detect)
# Retorna: BulkImportResult

# POST /api/v1/measurements/import/json
# Content-Type: multipart/form-data
# Body: file (JSON)
# Retorna: BulkImportResult

# GET /api/v1/measurements/import/template/csv
# Retorna: arquivo CSV template para download

# GET /api/v1/measurements/import/{import_id}
# Retorna: BulkImportResult de uma importacao anterior

# GET /api/v1/measurements/import/{import_id}/errors/csv
# Retorna: CSV apenas com as linhas que tiveram erro (para correcao e re-importacao)
```

### 3.5 Configuracao

```env
INTELLICARE_DONABEDIAN_IMPORT_MAX_ROWS=10000
INTELLICARE_DONABEDIAN_IMPORT_MAX_FILE_MB=10
INTELLICARE_DONABEDIAN_IMPORT_ALLOW_OVERWRITE=false  # Nao sobrescreve duplicatas
```

## 4. Testes

- BulkImportService.import_csv: valido, encoding Latin-1, com erros parciais (4 testes)
- BulkImportService.import_json: valido, malformado (2 testes)
- validate_row: campo obrigatorio ausente, indicator nao existe, periodo invalido (4 testes)
- check_duplicates: detecta duplicata, aceita medicao nova (2 testes)
- Endpoints: csv upload, json upload, template, errors (4 testes)
- Limite de linhas: rejeita > 10.000 (1 teste)
- **Total**: 17+ testes novos

## 5. Criterios de Aceitacao

- [ ] `BulkImportService` com suporte a CSV e JSON
- [ ] Auto-detect de encoding (UTF-8, Latin-1, Windows-1252)
- [ ] Auto-detect de separador CSV (';' e ',')
- [ ] Relatorio detalhado de erros por linha
- [ ] Duplicatas ignoradas com aviso (sem sobrescrever)
- [ ] Template CSV disponivel para download
- [ ] CSV de erros para re-importacao apos correcao
- [ ] Limite de 10.000 linhas com rejeicao clara
- [ ] 5 endpoints REST funcionais
- [ ] 363 testes v1.0 continuam passando
- [ ] 17+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `services/bulk_import.py`, `api/routes/import_routes.py`, `data/templates/medicoes_template.csv`
- **Arquivos modificados**: `api/main.py`, `config.py`
- **Linhas estimadas**: ~400
- **Testes novos**: ~17
- **Dependencias novas**: `chardet` (auto-detect encoding)
