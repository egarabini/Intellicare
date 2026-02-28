# intellicare-geralda

Agente de **Acompanhamento do Paciente** do IntelliCare — homenagem a **Geralda Lopes da Silva**, enfermeira pioneira na saude comunitaria brasileira.

## O que faz

- **Planos de Cuidado**: Cria e gerencia planos personalizados por paciente
- **Tarefas Diarias**: Medicamentos, exercicios, dieta, exames, monitoramento
- **Lembretes**: Sistema de lembretes com frequencias (unico, diario, semanal, mensal)
- **Educacao em Saude**: Materiais educativos para DRC, Diabetes e Hipertensao
- **Adesao**: Calcula taxa de adesao do paciente ao plano de cuidado

## Quick Start

```bash
# Instalar
pip install -e ".[dev]"

# Rodar API
uvicorn geralda.api.app:app --reload --port 8000

# Rodar testes
pytest tests/ -v --cov=geralda

# Docker
docker compose up --build
```

## API Endpoints

### Contrato LEGO
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/info` | Informacoes do modulo |

### Planos de Cuidado
| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/v1/plans` | Criar plano |
| GET | `/api/v1/plans` | Listar planos |
| GET | `/api/v1/plans/{plan_id}` | Obter plano |

### Tarefas
| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/v1/plans/{plan_id}/tasks` | Adicionar tarefa |
| GET | `/api/v1/plans/{plan_id}/tasks` | Listar tarefas |
| POST | `/api/v1/tasks/{task_id}/complete` | Completar tarefa |
| POST | `/api/v1/tasks/{task_id}/skip` | Pular tarefa |

### Lembretes
| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/v1/reminders` | Criar lembrete |
| GET | `/api/v1/reminders?patient_id=X` | Listar lembretes |
| GET | `/api/v1/reminders/due?patient_id=X` | Lembretes do dia |
| GET | `/api/v1/reminders/schedule?patient_id=X` | Agenda diaria |
| POST | `/api/v1/reminders/{id}/pause` | Pausar |
| POST | `/api/v1/reminders/{id}/resume` | Retomar |
| POST | `/api/v1/reminders/{id}/cancel` | Cancelar |

### Adesao
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/adherence/{plan_id}` | Calculo de adesao |

### Educacao em Saude
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/education/conditions` | Listar condicoes |
| GET | `/api/v1/education/{code}` | Materiais por condicao |
| GET | `/api/v1/education/material/{id}` | Material especifico |
| GET | `/api/v1/education/search?q=X` | Buscar materiais |

## Estrutura

```
intellicare-geralda/
  geralda/
    config.py              # GeraldaConfig (pydantic-settings)
    api/
      app.py               # FastAPI (24 endpoints)
    engine/
      models.py            # CareTask, CarePlan, Reminder, EducationContent, PatientAdherence
      care_manager.py      # Planos + tarefas + adesao
      reminder_engine.py   # Lembretes com scheduling
      education/
        content_loader.py  # Loader de YAML educativos
        data/
          ckd.yaml         # 3 materiais DRC
          dm2.yaml         # 4 materiais Diabetes
          has.yaml         # 4 materiais Hipertensao
  tests/                   # 108 testes, 96% cobertura
  Dockerfile
  docker-compose.yml       # Porta 8006
```

## Testes

```
108 passed — 96% coverage
- test_models.py        (18 testes) — modelos de dados
- test_care_manager.py  (20 testes) — planos e tarefas
- test_reminder_engine.py (20 testes) — lembretes
- test_content_loader.py (17 testes) — educacao
- test_config.py         (2 testes) — configuracao
- test_api.py           (27 testes) — API REST
```

## Condicoes Suportadas

| Codigo | Nome | Materiais |
|--------|------|-----------|
| N18 | Doenca Renal Cronica | 3 (basico/intermediario) |
| E11 | Diabetes Mellitus Tipo 2 | 4 (basico/intermediario) |
| I10 | Hipertensao Arterial | 4 (basico/intermediario) |

## Porta

| Servico | Porta |
|---------|-------|
| API | 8006 (host) -> 8000 (container) |
