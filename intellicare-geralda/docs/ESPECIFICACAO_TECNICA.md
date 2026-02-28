# intellicare-geralda — Especificacao Tecnica

## 1. Estrutura

```
intellicare-geralda/
├── geralda/
│   ├── __init__.py
│   ├── config.py
│   ├── api/
│   │   ├── app.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── careplan.py      # Planos de cuidado
│   │       ├── reminders.py     # Lembretes
│   │       └── education.py     # Materiais educativos
│   ├── engine/
│   │   ├── care_manager.py      # Gestao de cuidado
│   │   ├── reminder_engine.py   # Motor de lembretes
│   │   ├── education/
│   │   │   ├── content_generator.py
│   │   │   └── templates/       # Templates por condicao
│   │   └── communication/
│   │       └── messaging.py     # Canal de comunicacao
│   ├── ui/
│   │   ├── patient_app.py       # Interface do paciente
│   │   └── team_dashboard.py    # Painel da equipe
│   └── subagent/
│       └── geralda_subagent.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 2. Maturidade Atual: 0/10 (conceito apenas)

## 3. Diferenciais Tecnicos

- FHIR CarePlan como modelo de dados principal
- NLP para simplificacao de linguagem medica
- Templates de educacao em saude por condicao cronica
