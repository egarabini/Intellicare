# EF-013 — Pre e Pos Consulta

> Preparacao inteligente antes da consulta e acompanhamento estruturado apos a consulta.

## 1. Objetivo

Implementar fluxos automatizados de pre e pos-consulta que:
- Preparam o paciente antes da consulta (checklist, orientacoes, exames)
- Geram resumo clinico simplificado para o paciente levar
- Lembram o paciente de perguntas a fazer ao medico
- Registram orientacoes pos-consulta em linguagem acessivel
- Criam tarefas de follow-up baseadas nas orientacoes
- Ajustam plano de cuidado com base nas novas orientacoes

## 2. Justificativa

- **Preparo**: Paciente preparado aproveita melhor a consulta
- **Continuidade**: Orientacoes pos-consulta nao se perdem
- **Empoderamento**: Paciente sabe o que perguntar e o que esperar
- **Rastreabilidade**: Cada consulta gera acoes de follow-up
- **Qualidade**: Indicador Donabedian — preparacao melhora desfecho

## 3. Escopo

### 3.1 Fluxo Pre-Consulta

```
Consulta agendada (D-7 a D-1)
    │
    ▼
┌───────────────────────────────────┐
│  PRE-CONSULTA                     │
│                                   │
│  D-7: Lembrete inicial           │
│  D-3: Checklist de preparacao    │
│  D-1: Resumo + perguntas        │
│  D-0: Lembrete final + link     │
│       (se teleconsulta)          │
└───────────────────────────────────┘
    │
    ▼
Consulta realizada
    │
    ▼
┌───────────────────────────────────┐
│  POS-CONSULTA                     │
│                                   │
│  D+0: Registrar orientacoes      │
│  D+0: Criar tarefas de follow-up │
│  D+1: Enviar resumo ao paciente  │
│  D+3: Verificar compreensao      │
│  D+7: Acompanhar adesao          │
└───────────────────────────────────┘
```

### 3.2 Motor de Pre-Consulta

```python
class PreConsultationEngine:
    """Motor de preparacao para consultas."""

    async def prepare_consultation(
        self,
        patient_id: str,
        consultation_id: str,
        consultation_date: datetime,
        consultation_type: str,      # presencial, teleconsulta
        specialist: str,             # nefrologista, endocrinologista, etc.
        conditions: list[str],       # ICD-10 das condicoes relevantes
    ) -> PreConsultationPlan:
        """
        Gera plano completo de pre-consulta.

        Returns:
            PreConsultationPlan com:
            - checklist de preparacao
            - exames necessarios
            - perguntas sugeridas
            - resumo clinico simplificado
            - lembretes agendados
        """

    async def generate_preparation_checklist(
        self,
        patient_id: str,
        specialist: str,
        conditions: list[str],
    ) -> list[ChecklistItem]:
        """
        Gera checklist personalizado por especialidade.

        Exemplos por especialista:

        Nefrologista:
        - [ ] Levar resultados de creatinina/ureia recentes
        - [ ] Anotar medicamentos atuais e dosagens
        - [ ] Medir pressao arterial nos ultimos 3 dias
        - [ ] Registrar ingesta de liquidos dos ultimos 7 dias
        - [ ] Jejum de 12h se exame agendado

        Endocrinologista:
        - [ ] Levar resultados de HbA1c e glicemia
        - [ ] Trazer registro de glicemia capilar (se fizer)
        - [ ] Anotar episodios de hipo/hiperglicemia
        - [ ] Listar medicamentos e insulinas

        Cardiologista:
        - [ ] Levar ECG recente (se houver)
        - [ ] Anotar pressao arterial dos ultimos 7 dias
        - [ ] Registrar episodios de dor no peito, falta de ar
        - [ ] Trazer lista de medicamentos
        """

    async def generate_suggested_questions(
        self,
        patient_id: str,
        conditions: list[str],
        patient_concerns: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Gera perguntas sugeridas para o paciente fazer ao medico.

        Usa LLM para personalizar baseado em:
        - Condicoes do paciente
        - Estagio da doenca (via Oswaldo)
        - Ultimos exames (via Florence)
        - Preocupacoes do paciente (se informadas)
        - Adesao ao tratamento

        Exemplos para DRC:
        - "Doutor, meus rins estao melhores ou piores?"
        - "Preciso mudar algum medicamento?"
        - "Posso comer [alimento especifico]?"
        - "Quando vou precisar de dialise?"
        - "Tenho que repetir algum exame?"
        """

    async def generate_patient_summary(
        self,
        patient_id: str,
        reading_level: str = "basico",
    ) -> PatientSummary:
        """
        Gera resumo clinico em linguagem acessivel para o paciente levar.

        Formato:
        ┌─────────────────────────────────────┐
        │  MEU RESUMO DE SAUDE               │
        │  Preparado para: Joao da Silva      │
        │  Consulta: Dra. Ana (Nefrologia)    │
        │  Data: 20/02/2026                    │
        │                                     │
        │  MINHAS CONDICOES:                  │
        │  • Doenca Renal Cronica (estagio 3a)│
        │  • Diabetes tipo 2                   │
        │  • Pressao alta                      │
        │                                     │
        │  MEUS MEDICAMENTOS:                 │
        │  • Losartana 50mg - 1x ao dia       │
        │  • Metformina 850mg - 2x ao dia     │
        │  • AAS 100mg - 1x ao dia            │
        │                                     │
        │  ULTIMOS EXAMES:                    │
        │  • Creatinina: 1.8 (15/01/2026)     │
        │  • HbA1c: 7.1% (10/01/2026)        │
        │  • Pressao: 140/90 (media 7 dias)   │
        │                                     │
        │  COMO ESTOU ME CUIDANDO:            │
        │  • Tomando medicamentos: 85% ✓       │
        │  • Exercicio: 60% ↓                  │
        │  • Dieta: Bom                        │
        │                                     │
        │  MINHAS DUVIDAS:                    │
        │  1. ___________________________     │
        │  2. ___________________________     │
        │  3. ___________________________     │
        └─────────────────────────────────────┘
        """
```

### 3.3 Motor de Pos-Consulta

```python
class PostConsultationEngine:
    """Motor de acompanhamento pos-consulta."""

    async def register_post_consultation(
        self,
        patient_id: str,
        consultation_id: str,
        post_data: PostConsultationData,
    ) -> PostConsultationResult:
        """
        Registra dados pos-consulta.

        post_data:
            - notes: Anotacoes do profissional
            - new_medications: Medicamentos novos/alterados
            - discontinued_medications: Medicamentos suspensos
            - new_exams_requested: Exames solicitados
            - referrals: Encaminhamentos
            - next_appointment: Proximo retorno
            - restrictions: Novas restricoes
            - instructions: Orientacoes textuais

        Acoes automaticas:
        1. Ajustar lembretes (novos medicamentos, suspensoes)
        2. Criar tarefas de follow-up
        3. Agendar exames solicitados
        4. Atualizar plano de cuidado
        5. Gerar resumo simplificado para o paciente
        """

    async def generate_patient_instructions(
        self,
        consultation_notes: str,
        patient_id: str,
        reading_level: str = "basico",
    ) -> str:
        """
        Converte anotacoes medicas em orientacoes para o paciente via LLM.

        Entrada (nota medica):
        "Pct com DRC G3aA2, TFG 45, Cr 1.8. Ajuste de Losartana para 100mg.
         Solicitar US renal + PTH. Retorno 90d. Dieta hipoproteica."

        Saida (linguagem acessivel):
        "Joao, na consulta de hoje o doutor verificou que seus rins estao
         estaveis. Algumas mudancas importantes:

         💊 MEDICAMENTOS:
         • Losartana: agora voce vai tomar 100mg (era 50mg)
           - Continue tomando 1 vez ao dia, de manha

         🔬 EXAMES PEDIDOS:
         • Ultrassom dos rins — agendar no posto
         • Exame de sangue (PTH) — agendar no laboratorio

         🍽️ ALIMENTACAO:
         • Comer menos carne e proteina
         • O material sobre dieta sera enviado amanha

         📅 PROXIMO RETORNO:
         • Daqui 3 meses (maio/2026)
         • Trazer resultados dos exames

         ⚠️ IMPORTANTE:
         Se sentir tontura, inchaço subito nas pernas ou
         diminuicao na urina, procure o pronto-socorro."
        """

    async def create_follow_up_tasks(
        self,
        patient_id: str,
        post_data: PostConsultationData,
    ) -> list[str]:
        """
        Cria tarefas de follow-up no plano de cuidado.

        Tarefas automaticas:
        - Novo medicamento → Lembrete + material educativo
        - Exame solicitado → Lembrete para agendar + preparo
        - Encaminhamento → Lembrete + orientacao
        - Retorno → Lembrete D-7 + D-1
        - Restricao → Material educativo + lembrete
        """
```

### 3.4 Acompanhamento Pos-Consulta (D+1 a D+7)

```python
class PostConsultationFollowUp:
    """Acompanhamento nos dias apos a consulta."""

    async def day_plus_1(self, patient_id: str) -> None:
        """
        D+1: Enviar resumo simplificado.

        - Resumo das orientacoes em linguagem acessivel
        - Confirmar que entendeu as mudancas
        - Perguntar se tem duvidas
        """

    async def day_plus_3(self, patient_id: str) -> None:
        """
        D+3: Verificar compreensao.

        - Quiz rapido sobre orientacoes principais
        - Verificar se iniciou novo medicamento
        - Verificar se agendou exames
        """

    async def day_plus_7(self, patient_id: str) -> None:
        """
        D+7: Acompanhar adesao.

        - Verificar adesao ao novo esquema
        - Verificar se exames foram agendados
        - Verificar se encaminhamentos foram seguidos
        - Gerar alerta se nenhuma acao foi tomada
        """
```

### 3.5 Tabelas

```sql
-- Consultas (vinculo com pre/pos)
CREATE TABLE consultations (
    id BIGSERIAL PRIMARY KEY,
    consultation_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    journey_id UUID,
    consultation_type VARCHAR(20) NOT NULL,  -- presencial, teleconsulta
    specialist VARCHAR(100),
    scheduled_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, completed, missed, cancelled
    completed_at TIMESTAMPTZ,

    -- Pre-consulta
    pre_checklist JSONB DEFAULT '[]',
    pre_questions JSONB DEFAULT '[]',
    pre_summary_sent BOOLEAN DEFAULT FALSE,

    -- Pos-consulta
    post_notes TEXT,
    post_instructions TEXT,
    post_new_medications JSONB DEFAULT '[]',
    post_exams_requested JSONB DEFAULT '[]',
    post_referrals JSONB DEFAULT '[]',
    post_restrictions JSONB DEFAULT '[]',
    next_appointment TIMESTAMPTZ,

    -- Follow-up
    followup_d1_sent BOOLEAN DEFAULT FALSE,
    followup_d3_sent BOOLEAN DEFAULT FALSE,
    followup_d7_sent BOOLEAN DEFAULT FALSE,
    comprehension_score FLOAT,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consultations_patient ON consultations(patient_id);
CREATE INDEX idx_consultations_date ON consultations(scheduled_date);
CREATE INDEX idx_consultations_status ON consultations(status);
```

### 3.6 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/consultation/prepare` | Iniciar preparacao pre-consulta |
| GET | `/api/v1/consultation/{id}/checklist` | Checklist de preparacao |
| GET | `/api/v1/consultation/{id}/questions` | Perguntas sugeridas |
| GET | `/api/v1/consultation/{id}/summary` | Resumo para o paciente |
| POST | `/api/v1/consultation/{id}/post` | Registrar pos-consulta |
| GET | `/api/v1/consultation/{id}/instructions` | Orientacoes simplificadas |
| GET | `/api/v1/consultation/patient/{patient_id}` | Historico de consultas |
| POST | `/api/v1/consultation/{id}/comprehension` | Resultado do quiz D+3 |

### 3.7 Integracao com Outros Componentes

| Componente | Relacao |
|------------|---------|
| EF-003 (Ollama) | LLM gera perguntas, resumos, orientacoes |
| EF-004 (Linguagem) | Simplifica notas medicas |
| EF-005 (Educacao) | Material educativo pos-consulta |
| EF-006 (Eventos) | `operational.consultation_scheduled/completed` |
| EF-007 (Contextos) | Contexto ativo durante pre/pos |
| EF-010 (Florence) | Dados de exames para resumo |
| EF-010 (Oswaldo) | Estagiamento para contexto |
| EF-011 (Comunicacao) | Envio de mensagens/lembretes |
| EF-016 (Agendamento) | Teleconsulta agendada |

## 4. Testes

- PreConsultationEngine: prepare, checklist por especialidade, perguntas (8 testes)
- PatientSummary: geracao, por condicao, reading levels (5 testes)
- PostConsultationEngine: registrar, instructions, follow-up tasks (8 testes)
- PostConsultationFollowUp: D+1, D+3, D+7 (5 testes)
- LLM integration: notas → orientacoes, mock de LLM (4 testes)
- Endpoints: todos 8 (6 testes)
- Integracao: fluxo completo pre → consulta → pos → follow-up (3 testes)
- **Total**: 39+ testes

## 5. Criterios de Aceitacao

- [ ] Checklist pre-consulta por especialidade (nefro, endocrino, cardio)
- [ ] Perguntas sugeridas personalizadas via LLM
- [ ] Resumo clinico em linguagem acessivel ("Meu Resumo de Saude")
- [ ] Cronograma de lembretes (D-7, D-3, D-1, D-0)
- [ ] Registro pos-consulta com notas do profissional
- [ ] Orientacoes simplificadas geradas via LLM
- [ ] Tarefas de follow-up criadas automaticamente
- [ ] Follow-up D+1, D+3, D+7 automatizado
- [ ] Quiz de compreensao D+3
- [ ] 8 endpoints funcionais
- [ ] 39+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~5 (api, scheduler, care_manager, reminder_engine, docker)
- **Linhas estimadas**: ~2.000
- **Testes novos**: ~39
