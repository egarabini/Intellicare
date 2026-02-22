# EF-D002 — Relatorios de Qualidade

> Gerar relatorios executivos em PDF e HTML com avaliacao dos 7 pilares, comparativo entre periodos e recomendacoes para gestores de saude.

## 1. Objetivo

Implementar geracao de relatorios de qualidade assistencial exportaveis, permitindo que gestores:
- Levem relatorios para reunioes de qualidade e comites hospitalares
- Comparem trimestre atual vs anterior (ou ano vs ano)
- Recebam recomendacoes priorizadas por impacto
- Compartilhem via PDF com stakeholders externos

## 2. Justificativa

- Gap critico identificado: 0% implementado
- Gestores nao operam apenas no dashboard — precisam de documentos para reunioes
- ANS e auditorias hospitalares exigem relatorios formais de qualidade
- Comparativo de periodos e fundamental para ciclo de melhoria continua (PDCA)

## 3. Escopo

### 3.1 Modelos de Relatorio

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import date


class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"           # Para integracao com outros sistemas


class ReportType(str, Enum):
    EXECUTIVE = "executive"         # Resumo de 1-2 paginas para diretoria
    FULL = "full"                   # Relatorio completo com todos os pilares
    COMPARATIVE = "comparative"     # Comparativo entre dois periodos
    PILLAR = "pillar"               # Relatorio de um pilar especifico


@dataclass
class ReportPeriod:
    start_date: date
    end_date: date
    label: str               # Ex: "Q4-2025", "2025", "Jan-Mar 2026"


@dataclass
class QualityReport:
    """
    Definicao de um relatorio gerado.
    """
    report_id: str           # UUID
    report_type: ReportType
    format: ReportFormat

    period: ReportPeriod
    comparison_period: Optional[ReportPeriod]  # Para relatorios comparativos

    # Conteudo
    overall_score: float
    overall_status: str
    pillar_scores: dict
    triad_scores: dict
    critical_indicators: list[dict]
    improving_areas: list[str]
    declining_areas: list[str]
    recommendations: list[dict]     # Priorizadas por impacto

    # Comparativo (se applicable)
    score_delta: Optional[float]    # Score atual - periodo anterior
    improved_pillars: Optional[list[str]]
    declined_pillars: Optional[list[str]]

    # Metadados
    generated_at: str
    generated_by: Optional[str]     # usuario/agente que solicitou
    file_path: Optional[str]        # Path do arquivo gerado
```

### 3.2 QualityReportService

```python
class QualityReportService:
    """
    Gera relatorios de qualidade em PDF/HTML.

    Biblioteca: WeasyPrint (HTML → PDF via CSS)
    Templates: Jinja2 com template HTML do IntelliCare
    Graficos: Plotly figuras exportadas como imagem base64

    Cache: relatorio em disco por 24h (nao regenera se ja existe)
    """

    REPORT_OUTPUT_DIR = "/tmp/donabedian_reports"
    REPORT_CACHE_HOURS = 24

    async def generate_executive_report(
        self,
        period: ReportPeriod,
        format: ReportFormat = ReportFormat.PDF,
    ) -> QualityReport:
        """
        Relatorio executivo — 2 paginas.

        Conteudo:
        1. Score geral com semaforo
        2. Radar dos 7 pilares (imagem Plotly)
        3. Top 3 indicadores criticos
        4. Top 3 recomendacoes prioritarias
        5. Tendencia vs periodo anterior (setas)

        Tempo de geracao: < 10s
        """

    async def generate_full_report(
        self,
        period: ReportPeriod,
        format: ReportFormat = ReportFormat.PDF,
    ) -> QualityReport:
        """
        Relatorio completo — 8-15 paginas.

        Conteudo:
        1. Sumario executivo
        2. Avaliacao por pilar (1 pagina por pilar)
        3. Avaliacao pela triada (Estrutura/Processo/Resultado)
        4. Lista completa de indicadores com status
        5. Timeline dos ultimos 12 meses
        6. Recomendacoes priorizadas
        7. Glossario de termos

        Tempo de geracao: < 30s
        """

    async def generate_comparative_report(
        self,
        current_period: ReportPeriod,
        previous_period: ReportPeriod,
        format: ReportFormat = ReportFormat.PDF,
    ) -> QualityReport:
        """
        Relatorio comparativo entre dois periodos.

        Conteudo:
        1. Variacao geral (score atual vs anterior, delta)
        2. Tabela comparativa por pilar (colunas: periodo1, periodo2, delta, tendencia)
        3. Indicadores que melhoraram / pioraram
        4. Analise do que impulsionou a mudanca
        5. Recomendacoes para o proximo periodo

        Util para: reunioes trimestrais, relatorios anuais.
        """

    async def generate_pillar_report(
        self,
        pillar_id: str,
        period: ReportPeriod,
        format: ReportFormat = ReportFormat.PDF,
    ) -> QualityReport:
        """
        Relatorio aprofundado de um pilar especifico.

        Conteudo:
        1. Definicao e importancia do pilar
        2. Indicadores do pilar com status
        3. Timeline do pilar (12 meses)
        4. Comparacao com benchmarks (quando disponivel)
        5. Recomendacoes especificas
        """

    def _build_recommendations(
        self,
        quality_data: dict,
    ) -> list[dict]:
        """
        Gera recomendacoes priorizadas por impacto.

        Logica:
        1. Indicadores em VERMELHO → recomendacao URGENTE
        2. Pilares abaixo de 60 → recomendacao de melhoria
        3. Tendencia de piora → recomendacao preventiva
        4. Benchmark abaixo da media → recomendacao de ajuste

        Cada recomendacao inclui:
        {
            "priority": "alta",
            "pillar": "eficiencia",
            "action": "Revisar processo de prescricao para reduzir tempo internacao",
            "indicator_trigger": "Tempo medio de permanencia (8.2d, meta <6d)",
            "expected_impact": "Reducao de custo e melhoria no pilar Eficiencia",
            "timeline": "30-60 dias"
        }
        """
```

### 3.3 Templates HTML/PDF

```
src/donabedian/
  reports/
    templates/
      executive_report.html      # Template executivo (2 paginas)
      full_report.html           # Template completo (multi-pagina)
      comparative_report.html    # Template comparativo
      pillar_report.html         # Template por pilar
      _base.html                 # Base com header/footer IntelliCare
      _styles.css                # Estilos (cores IntelliCare, tipografia)
    service.py                   # QualityReportService
    renderer.py                  # HTML/PDF rendering via WeasyPrint
    chart_exporter.py            # Plotly → base64 PNG para PDF
```

### 3.4 Endpoints REST Novos

```python
# POST /api/v1/reports/executive
# Body: {period_start, period_end, format: "pdf"/"html"}
# Retorna: file (PDF ou HTML)

# POST /api/v1/reports/full
# Body: {period_start, period_end, format}
# Retorna: file

# POST /api/v1/reports/comparative
# Body: {current_start, current_end, previous_start, previous_end, format}
# Retorna: file

# POST /api/v1/reports/pillar/{pillar_id}
# Body: {period_start, period_end, format}
# Retorna: file

# GET /api/v1/reports/{report_id}/download
# Retorna: file do relatorio ja gerado (cache 24h)

# GET /api/v1/reports/history
# Retorna: lista de relatorios gerados com metadados
```

### 3.5 Configuracao

```env
INTELLICARE_DONABEDIAN_REPORTS_DIR=/tmp/donabedian_reports
INTELLICARE_DONABEDIAN_REPORTS_CACHE_HOURS=24
INTELLICARE_DONABEDIAN_REPORTS_ENABLED=true
```

## 4. Testes

- QualityReportService: executive, full, comparative (4 testes)
- _build_recommendations: indicadores vermelhos priorizados (3 testes)
- Endpoints: cada tipo de relatorio (4 testes)
- Template rendering: HTML valido (2 testes)
- PDF gerado: arquivo existe e nao e vazio (2 testes)
- Cache: relatorio reutilizado (2 testes)
- **Total**: 17+ testes novos

## 5. Criterios de Aceitacao

- [ ] `QualityReportService` com 4 tipos de relatorio
- [ ] PDF gerado com radar dos 7 pilares (imagem Plotly)
- [ ] Relatorio comparativo com delta por pilar
- [ ] Recomendacoes priorizadas por urgencia (vermelho primeiro)
- [ ] 5 endpoints REST de geracao e download
- [ ] Cache de 24h por relatorio (nao regenera desnecessariamente)
- [ ] Templates em portugues com logo IntelliCare
- [ ] 363 testes v1.0 continuam passando
- [ ] 17+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `reports/service.py`, `reports/renderer.py`, `reports/chart_exporter.py`, 4 templates HTML, `api/routes/reports.py`
- **Arquivos modificados**: `api/main.py`, `config.py`
- **Linhas estimadas**: ~600
- **Testes novos**: ~17
- **Dependencias novas**: `weasyprint`, `jinja2`, `kaleido` (Plotly export)
