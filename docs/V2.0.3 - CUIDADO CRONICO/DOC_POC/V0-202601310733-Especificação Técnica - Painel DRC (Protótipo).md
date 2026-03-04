# Especificação Técnica - Painel DRC (Protótipo)

**Documento:** V0-20260131-EspecificacaoTecnica.md
**Projeto:** Painel DRC (Protótipo)
**Versão:** 1.0
**Data:** 31 de Janeiro de 2026
**Elaboração:** Manus AI (Planejador)

Este documento detalha a **Especificação Técnica** para o desenvolvimento do protótipo do Painel DRC, traduzindo os requisitos funcionais em uma arquitetura de software concreta baseada em Python.

## 1. Visão Geral e Dependências

### 1.1. Stack Tecnológica
| Componente | Tecnologia | Módulo Python | Função |
| :--- | :--- | :--- | :--- |
| **Frontend** | Streamlit | `src/ui/` | Interface do usuário e visualização de dados. |
| **Validação** | FHIR R4 | `fhir.resources` | Modelagem e validação de dados FHIR (Pydantic). |
| **Cache** | LMDB | `lmdb` | Cache de alta performance para lookups por ID. |
| **Persistência** | PostgreSQL | `psycopg2` ou `SQLAlchemy` | Banco de dados persistente para dados FHIR. |
| **Lógica** | Python | `src/core/` | Regras de negócio (cálculo de eGFR, alertas). |

### 1.2. Configuração do PostgreSQL
O sistema deve se conectar ao PostgreSQL para persistência de dados. As credenciais devem ser carregadas de variáveis de ambiente ou de um arquivo `.env` (não versionado).

| Parâmetro | Valor |
| :--- | :--- |
| **Host** | `161.97.141.186` |
| **Porta** | `5432` |
| **Banco de Dados** | `DRCDbDEV` |
| **Usuário** | `admin_drcdb` |
| **Senha** | `Crazy#57LB` |

## 2. Arquitetura de Classes Python

A arquitetura será dividida em três camadas principais: **Acesso a Dados (DAL)**, **Lógica de Negócio (Core)** e **Apresentação (UI)**.

### 2.1. Camada de Acesso a Dados (DAL) - `src/api/`

Esta camada será responsável por toda a comunicação com o Servidor FHIR (ou o mock FHIR/PostgreSQL/LMDB).

#### Classe `FHIRDataStore`
Esta classe atuará como um *facade* para as operações de CRUD e Search, decidindo se busca no cache LMDB ou no banco de dados persistente.

```python
# src/api/fhir_datastore.py

import lmdb
from fhir.resources.core.fhirabstractmodel import FHIRAbstractModel
from typing import Optional, Type

class FHIRDataStore:
    def __init__(self, db_url: str, lmdb_path: str, lmdb_map_size: int = 10**9):
        """Inicializa as conexões com PostgreSQL e LMDB."""
        self.db_url = db_url  # Conexão com PostgreSQL (via SQLAlchemy/psycopg2)
        self.lmdb_env = lmdb.open(lmdb_path, map_size=lmdb_map_size)
        # Inicialização da conexão com o PostgreSQL (a ser detalhada na implementação)

    def get_resource(self, resource_type: Type[FHIRAbstractModel], resource_id: str) -> Optional[FHIRAbstractModel]:
        """Busca um recurso por ID, priorizando o cache LMDB."""
        key = f"{resource_type.__name__}:{resource_id}".encode('utf-8')
        
        # 1. Tenta buscar no LMDB (Cache)
        with self.lmdb_env.begin() as txn:
            cached_data = txn.get(key)
            if cached_data:
                # Retorna o recurso validado pelo fhir.resources
                return resource_type.parse_raw(cached_data)

        # 2. Se não estiver no cache, busca no PostgreSQL (Persistência)
        # Lógica de busca no PostgreSQL (SQLAlchemy/psycopg2)
        # ...
        
        # 3. Se encontrado no DB, armazena no LMDB e retorna
        # ...
        
        return None

    def search_resources(self, resource_type: Type[FHIRAbstractModel], query_params: dict) -> list[FHIRAbstractModel]:
        """Realiza buscas complexas (longitudinais) diretamente no PostgreSQL."""
        # Esta operação ignora o LMDB e usa o PostgreSQL otimizado para queries.
        # Lógica de conversão de query FHIR para SQL (a ser detalhada)
        # ...
        pass

    def save_resource(self, resource: FHIRAbstractModel):
        """Salva o recurso no PostgreSQL e atualiza o LMDB."""
        # 1. Valida o recurso usando fhir.resources
        resource.validate()
        
        # 2. Salva no PostgreSQL
        # ...
        
        # 3. Atualiza o LMDB
        key = f"{resource.resource_type}:{resource.id}".encode('utf-8')
        with self.lmdb_env.begin(write=True) as txn:
            txn.put(key, resource.json().encode('utf-8'))
            
        # 4. Gera e salva o recurso Provenance (se for um recurso clínico)
        # ...
```

### 2.2. Camada de Lógica de Negócio (Core) - `src/core/`

Esta camada contém a lógica específica da DRC, utilizando o `FHIRDataStore` para acesso a dados.

#### Classe `DRCCoreLogic`
```python
# src/core/drc_logic.py

from src.api.fhir_datastore import FHIRDataStore
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from typing import List

class DRCCoreLogic:
    def __init__(self, datastore: FHIRDataStore):
        self.datastore = datastore

    def get_patient_summary(self, patient_id: str) -> dict:
        """Agrega todos os dados necessários para o Resumo DRC (Monograph View)."""
        patient = self.datastore.get_resource(Patient, patient_id)
        
        # 1. Buscar Observações Longitudinais (eGFR, PA, ACR)
        eGFR_series = self.datastore.search_resources(Observation, {'patient': patient_id, 'code': '33914-3'})
        PA_series = self.datastore.search_resources(Observation, {'patient': patient_id, 'code': '85354-9'})
        
        # 2. Calcular Estágio DRC (Regra de Negócio)
        # Lógica para inferir o estágio G1-G5 e A1-A3
        
        # 3. Buscar Condições, Metas e Pendências
        # ...
        
        return {
            'patient': patient.dict(),
            'eGFR_data': [obs.dict() for obs in eGFR_series],
            'current_stage': 'G3aA2', # Exemplo
            # ...
        }

    def add_blood_pressure(self, patient_id: str, systolic: float, diastolic: float, date: str):
        """Cria um novo recurso Observation (Painel PA) e o salva."""
        # 1. Cria o recurso Observation usando fhir.resources
        # 2. Chama self.datastore.save_resource(new_observation)
        # ...
        pass
```

## 3. Estratégia de Acesso a Dados (LMDB e PostgreSQL)

### 3.1. Uso do LMDB (Cache)
O LMDB será usado exclusivamente para *lookups* por ID (`Patient/123`, `Observation/456`).
*   **Chave:** `[resource_type]:[resource_id]` (ex: `b'Patient:123'`).
*   **Valor:** O recurso FHIR completo serializado em JSON (`resource.json().encode('utf-8')`).
*   **Invalidação:** O cache é atualizado (ou invalidado) sempre que um recurso é salvo (`save_resource`).

### 3.2. Uso do PostgreSQL (Persistência)
O PostgreSQL será o *source of truth* e será usado para:
1.  **Buscas Complexas:** Todas as buscas longitudinais (`search_resources`) que envolvem filtros por código, data e paciente.
2.  **Persistência:** Armazenamento seguro de todos os recursos FHIR.

**Sugestão de Modelagem no PostgreSQL:**
Para simplificar o MVP, sugere-se uma tabela única para recursos FHIR, com colunas para indexação rápida:

| Coluna | Tipo | Uso |
| :--- | :--- | :--- |
| `id` | UUID | ID único do recurso (primário) |
| `resource_type` | VARCHAR | Tipo do recurso (Patient, Observation, etc.) |
| `patient_id` | UUID | Referência ao Patient (para indexação rápida) |
| `code` | VARCHAR | Código principal (LOINC/SNOMED) (para indexação rápida) |
| `created_at` | TIMESTAMP | Data de criação (para ordenação) |
| `data` | JSONB | O recurso FHIR completo em formato JSON. |

## 4. Próximos Passos para a Implementação

O Desenvolvedor IA deve focar na implementação dos seguintes módulos, em ordem:

1.  **Setup do Ambiente:** Criar o ambiente virtual, instalar dependências (`requirements.txt`) e configurar o arquivo `.env` com as credenciais do PostgreSQL.
2.  **Implementação do `FHIRDataStore`:** Focar primeiro na lógica de LMDB (cache) e na conexão básica com o PostgreSQL.
3.  **Implementação do `DRCCoreLogic`:** Criar a função `get_patient_summary` e as funções de registro rápido (`add_blood_pressure`, etc.).
4.  **Frontend Streamlit:** Criar o `main.py` e os componentes básicos da UI que chamam o `DRCCoreLogic`.
5.  **Geração de Dados:** Criar o *dataset* sintético de demonstração (JSON FHIR) para popular o banco de dados.
