# EF-Z001 — Enriquecimento CNES: Leitos, Profissionais e Servicos

> Adicionar ao CnesClient os endpoints de leitos, profissionais e servicos especializados, ja disponlveis na API publica do CNES.

## 1. Objetivo

Completar o cliente CNES com os tres endpoints de enriquecimento que estao na API publica mas ainda nao foram implementados:
- **Leitos**: quantos leitos tem um estabelecimento, por tipo (SUS, nao-SUS, cirurgico, obstetrico)
- **Profissionais**: quais profissionais de saude atuam no estabelecimento, por CBO
- **Servicos**: quais servicos especializados o estabelecimento oferece (quimio, dialise, UTI, etc.)

## 2. Justificativa

- **Capacidade instalada**: sem leitos/servicos, nao da pra saber se um hospital consegue atender encaminhamento
- **Encaminhamento inteligente**: Geralda + Wanda precisam saber "qual hospital proximo tem dialise e leito SUS disponivel?"
- **Vazios assistenciais** (EF-Z006): requer dados de capacidade para calcular cobertura
- **Baixa complexidade**: endpoints CNES ja existem — e apenas extensao do `cnes_client.py` existente

## 3. Escopo

### 3.1 Novos Modelos

```python
@dataclass
class HospitalBeds:
    """Distribuicao de leitos de um estabelecimento."""
    cnes_code: str
    total_beds: int
    sus_beds: int                    # Leitos SUS
    non_sus_beds: int                # Leitos nao-SUS / privados
    surgical_beds: int               # Leitos cirurgicos
    obstetric_beds: int              # Leitos obstetricos
    neonatal_beds: int               # Leitos neonatais
    icu_beds: int                    # UTI adulto
    icu_pediatric_beds: int          # UTI pediatrica
    icu_neonatal_beds: int           # UTI neonatal
    other_beds: int                  # Demais leitos

    def to_dict(self) -> dict: ...


@dataclass
class HealthProfessional:
    """Profissional de saude vinculado a estabelecimento."""
    cnes_code: str                   # CNES do estabelecimento
    cpf_hash: Optional[str]         # Hash SHA256 — nunca CPF direto
    cbo_code: str                   # Codigo CBO (ex: "225125" = Clinico Geral)
    cbo_description: str            # Descricao CBO
    professional_type: str          # Medico, Enfermeiro, etc.
    specialties: list[str]          # Especializacoes declaradas
    sus_bond: bool                  # Vinculo SUS
    active: bool

    def to_dict(self) -> dict: ...


@dataclass
class HealthService:
    """Servico especializado de um estabelecimento."""
    cnes_code: str
    service_code: str               # ex: "117" = Servico de Dialise
    service_description: str        # ex: "SERVICO DE DIALISE"
    classification_code: str        # Sub-classificacao
    classification_description: str
    sus_service: bool               # Oferece pelo SUS
    active: bool

    def to_dict(self) -> dict: ...


@dataclass
class EstablishmentDetail:
    """Visao completa de um estabelecimento com todos os dados."""
    establishment: HealthEstablishment
    beds: Optional[HospitalBeds]
    professionals_summary: Optional[dict]    # {cbo: count} — resumo
    services: Optional[list[HealthService]]

    def to_dict(self) -> dict: ...
    def has_service(self, service_code: str) -> bool: ...
    def has_icu(self) -> bool: ...
    def has_dialysis(self) -> bool: ...
    def total_sus_capacity(self) -> int: ...
```

### 3.2 Novos Metodos no CnesClient

```python
class CnesClient:
    # --- Metodos existentes permanecem inalterados ---

    def get_beds(
        self,
        cnes_code: str,
    ) -> Optional[HospitalBeds]:
        """
        Busca leitos de um estabelecimento.

        GET /cnes/leitos?codigo_cnes={cnes_code}

        Cache: 1 hora (dados mudam pouco)
        Retorna None se nao encontrado ou sem leitos.
        """

    def get_professionals(
        self,
        cnes_code: str,
        cbo_filter: Optional[str] = None,
        sus_only: bool = False,
        limit: int = 100,
    ) -> list[HealthProfessional]:
        """
        Busca profissionais de um estabelecimento.

        GET /cnes/profissionais?codigo_cnes={cnes_code}&cbo={cbo}&vinculo_sus={sus_only}

        PRIVACIDADE: CPF nunca armazenado — hash SHA256 apenas para deduplicacao.
        Cache: 6 horas (profissionais mudam com mais frequencia que leitos)
        Limit max: 100 por request (CNES pode ter muitos profissionais)
        """

    def get_services(
        self,
        cnes_code: str,
        sus_only: bool = False,
    ) -> list[HealthService]:
        """
        Busca servicos especializados do estabelecimento.

        GET /cnes/servicos?codigo_cnes={cnes_code}

        Cache: 24 horas (servicos mudam raramente)
        """

    def get_establishment_detail(
        self,
        cnes_code: str,
    ) -> Optional[EstablishmentDetail]:
        """
        Busca estabelecimento + leitos + resumo profissionais + servicos.

        Combina 3 chamadas paralelas (ou sequencial com cache).
        Retorna visao completa para encaminhamentos.
        """
```

### 3.3 Codigos de Servico Relevantes para IntelliCare

```python
# Codigos CNES de servicos especialmente relevantes
CRITICAL_SERVICES = {
    "117": "Dialise / Hemodialise",           # DRC — Oswaldo + Geralda
    "078": "Tratamento Quimioterapico",        # Oncologia
    "100": "UTI Adulto",                       # Critico
    "101": "UTI Pediatrica",
    "102": "UTI Neonatal",
    "103": "UTI Coronariana",                  # Cardiologia
    "119": "Transplante Renal",                # DRC avancada
    "136": "Programa de Saude da Familia",     # APS
    "148": "Atendimento ao Idoso",
    "149": "Saude Mental",
    "158": "Atendimento ao Diabetico",         # DM2 — Oswaldo
    "159": "Atendimento ao Hipertenso",        # HAS — Oswaldo
}
```

### 3.4 Novos Endpoints REST

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/establishment/{cnes}/beds` | Leitos do estabelecimento |
| GET | `/api/v1/establishment/{cnes}/professionals` | Profissionais (resumo por CBO) |
| GET | `/api/v1/establishment/{cnes}/services` | Servicos especializados |
| GET | `/api/v1/establishment/{cnes}/detail` | Visao completa (todos acima) |
| GET | `/api/v1/establishments/with-service` | Busca por servico (ex: todos com dialise) |

**Exemplo de uso critico:**
```
GET /api/v1/establishments/with-service?service_code=117&city_code=354990&sus_only=true

Resposta: lista de estabelecimentos com dialise SUS em Sao Paulo
```

### 3.5 Mudancas nos Modelos Existentes

`HealthEstablishment` ganha dois campos novos (opcionais, nao quebram v1.0):
```python
@dataclass
class HealthEstablishment:
    # ... campos existentes ...
    total_beds: Optional[int] = None      # Adicionado — preenchido quando disponivel
    available_services: list[str] = field(default_factory=list)  # Codigos de servico
```

### 3.6 Privacidade (LGPD)

- CPF de profissionais **nunca** armazenado diretamente
- Hash SHA256 usado apenas para deduplicacao interna
- Endpoint `/professionals` retorna contagem por CBO, nao dados pessoais
- Nomes de profissionais: retornar apenas se necessario (parcial — iniciais)

## 4. Testes

- HospitalBeds: to_dict, total_beds, sus_capacity (4 testes)
- HealthService: to_dict, has_service, has_dialysis (4 testes)
- EstablishmentDetail: to_dict, visao completa, sem leitos (3 testes)
- CnesClient.get_beds: found, not found, cached, API error (5 testes)
- CnesClient.get_professionals: found, cbo_filter, sus_only, limit (5 testes)
- CnesClient.get_services: found, sus_only, service codes (4 testes)
- CnesClient.get_establishment_detail: completo, parcial (3 testes)
- Novos endpoints REST: 5 endpoints (5 testes)
- LGPD: CPF nao exposto (2 testes)
- **Total**: 35+ testes novos

## 5. Criterios de Aceitacao

- [ ] Todos os 68 testes v1.0 continuam passando
- [ ] `get_beds()` funcional com cache de 1 hora
- [ ] `get_professionals()` sem expor CPF (LGPD)
- [ ] `get_services()` com mapeamento de codigos criticos
- [ ] `get_establishment_detail()` visao completa
- [ ] Endpoint `/establishments/with-service?service_code=117` para busca por dialise
- [ ] 35+ testes novos
- [ ] Cobertura >= 90%

## 6. Estimativa de Complexidade

- **Arquivos modificados**: `engine/models.py`, `engine/cnes_client.py`, `api/app.py`
- **Arquivos novos**: `engine/service_codes.py`
- **Linhas estimadas**: ~350
- **Testes novos**: ~35
