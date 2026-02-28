# EF-005 — Educacao Personalizada

> Geracao e adaptacao de conteudo educativo personalizado por IA para cada paciente.

## 1. Objetivo

Evoluir o sistema de educacao em saude (v1.0: 11 materiais YAML estaticos) para um motor inteligente que:
- Gera conteudo educativo sob demanda via LLM
- Personaliza materiais existentes ao perfil do paciente
- Cria trilhas de aprendizagem por condicao
- Avalia compreensao do paciente
- Sugere materiais baseado no momento da jornada

## 2. Justificativa

- **Personalizacao**: Cada paciente tem necessidades educativas diferentes
- **Lacunas**: 11 materiais nao cobrem todas as situacoes
- **Engajamento**: Conteudo relevante ao momento aumenta leitura
- **Escalabilidade**: IA gera conteudo sem depender de redator humano

## 3. Escopo

### 3.1 Arquitetura do Motor de Educacao

```
geralda/ai/education/
  __init__.py
  content_generator.py     # Gera conteudo via LLM
  learning_path.py         # Motor de trilhas de aprendizagem
  comprehension.py         # Avaliacao de compreensao
  recommendation.py        # Motor de recomendacao
```

### 3.2 Gerador de Conteudo Educativo

```python
class EducationContentGenerator:
    def __init__(self, llm: BaseChatModel, glossary: MedicalGlossary):
        self._llm = llm
        self._glossary = glossary

    async def generate_material(
        self,
        condition_code: str,
        topic: str,
        reading_level: str = "basico",
        patient_context: Optional[dict] = None,
    ) -> EducationContent:
        """
        Gera material educativo personalizado.

        Args:
            condition_code: ICD-10 (ex: "N18", "E11", "I10")
            topic: Tema (ex: "alimentacao", "medicamentos", "sinais de alerta")
            reading_level: Nivel de leitura do paciente
            patient_context: Dados do paciente para personalizacao

        Returns:
            EducationContent com conteudo gerado
        """

    async def personalize_existing(
        self,
        material_id: str,
        patient_context: dict,
        reading_level: str = "basico",
    ) -> EducationContent:
        """
        Personaliza material existente ao contexto do paciente.

        Exemplo: Material generico sobre DRC + dados reais do paciente
        = "Voce esta no estagio 3a. Isso significa que seus rins..."
        """

    async def generate_faq(
        self,
        condition_code: str,
        reading_level: str = "basico",
    ) -> list[dict]:
        """
        Gera FAQ (perguntas frequentes) sobre uma condicao.

        Returns:
            [{"question": "...", "answer": "..."}, ...]
        """
```

### 3.3 Trilha de Aprendizagem

Sequencia de materiais organizada por prioridade e momento da jornada:

```python
class LearningPath:
    def __init__(self, condition_code: str, patient_id: str):
        self.condition_code = condition_code
        self.patient_id = patient_id
        self.steps: list[LearningStep] = []

    async def generate(self) -> list[LearningStep]:
        """Gera trilha personalizada para o paciente."""

    def get_next_step(self) -> Optional[LearningStep]:
        """Retorna proximo material nao lido."""

    def mark_completed(self, step_id: str):
        """Marca material como lido."""

    def get_progress(self) -> dict:
        """Retorna progresso (ex: 3/7 materiais lidos, 43%)."""
```

**Exemplo de Trilha para DRC Estagio 3**:
| Ordem | Material | Momento | Obrigatorio |
|:---:|----------|---------|:-----------:|
| 1 | O que e Doenca Renal Cronica? | Diagnostico | Sim |
| 2 | Alimentacao para DRC | 1a semana | Sim |
| 3 | Seus medicamentos (personalizado) | 1a semana | Sim |
| 4 | Exames importantes na DRC | Antes da consulta | Sim |
| 5 | Como medir pressao em casa | 2a semana | Nao |
| 6 | Sinais de alerta | 2a semana | Sim |
| 7 | Perguntas para a proxima consulta | Pre-consulta | Nao |

### 3.4 Motor de Recomendacao

```python
class EducationRecommender:
    def recommend_for_patient(
        self,
        patient_id: str,
        conditions: list[str],
        journey_stage: str,
        materials_read: list[str],
    ) -> list[EducationContent]:
        """
        Recomenda materiais baseado em:
        - Condicoes ativas do paciente
        - Estagio da jornada (diagnostico, tratamento, acompanhamento)
        - Materiais ja lidos (nao repetir)
        - Nivel de leitura do paciente
        """

    def recommend_on_event(
        self,
        event_type: str,
        patient_context: dict,
    ) -> list[EducationContent]:
        """
        Recomenda material baseado em evento:
        - "exam_scheduled" → Material sobre o exame
        - "medication_changed" → Material sobre o novo medicamento
        - "adherence_low" → Material motivacional
        - "condition_worsened" → Material sobre sinais de alerta
        """
```

### 3.5 Avaliacao de Compreensao

```python
class ComprehensionAssessor:
    async def generate_quiz(
        self,
        material_id: str,
        num_questions: int = 3,
    ) -> list[dict]:
        """
        Gera quiz simples para verificar compreensao.

        Returns:
            [
                {
                    "question": "Qual a funcao principal dos rins?",
                    "options": ["Filtrar o sangue", "Produzir sangue", "Digertir alimentos"],
                    "correct": 0,
                    "explanation": "Os rins filtram o sangue, removendo toxinas..."
                }
            ]
        """

    async def evaluate_response(
        self,
        patient_answer: str,
        material_context: str,
    ) -> dict:
        """
        Avalia resposta aberta do paciente via LLM.

        Returns:
            {"understood": True/False, "feedback": "...", "suggestion": "..."}
        """
```

### 3.6 Tabela de Progresso Educativo

```sql
CREATE TABLE education_progress (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    material_id VARCHAR(20) NOT NULL,
    learning_path_id VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending',     -- pending, in_progress, completed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    comprehension_score FLOAT,                -- 0.0-1.0
    quiz_results JSONB,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_eduprogress_patient ON education_progress(patient_id);
```

### 3.7 Novos Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/education/generate` | Gera material personalizado via IA |
| GET | `/api/v1/education/path/{patient_id}` | Trilha de aprendizagem do paciente |
| POST | `/api/v1/education/path/{patient_id}/complete/{step_id}` | Marca passo como concluido |
| GET | `/api/v1/education/recommend/{patient_id}` | Recomendacoes para o paciente |
| POST | `/api/v1/education/quiz/{material_id}` | Gera quiz de compreensao |
| POST | `/api/v1/education/quiz/{material_id}/evaluate` | Avalia respostas |

## 4. Prompt para Geracao de Material

```python
EDUCATION_GENERATION_PROMPT = """
Voce e uma educadora em saude do sistema IntelliCare.

TAREFA: Crie material educativo sobre {topic} para pacientes com {condition}.

NIVEL DE LEITURA: {reading_level}
CONTEXTO DO PACIENTE: {patient_context}

REGRAS:
1. Linguagem {reading_level_rules}
2. Maximo 500 palavras
3. Use analogias do cotidiano
4. Inclua secao "O que voce pode fazer"
5. Inclua "Quando procurar ajuda"
6. NAO faca diagnosticos ou prescricoes
7. SEMPRE sugira conversar com o profissional de saude

FORMATO:
- Titulo
- Introducao (2-3 frases)
- Explicacao principal (3-5 paragrafos curtos)
- O que voce pode fazer (lista)
- Quando procurar ajuda (lista)
- Nota final acolhedora
"""
```

## 5. Testes

- ContentGenerator: geracao com LLM mockado (8 testes)
- Personalizacao de material existente (5 testes)
- LearningPath: geracao, progresso, next_step (8 testes)
- Recommender: por condicao, por evento, sem repeticao (8 testes)
- ComprehensionAssessor: quiz, avaliacao (5 testes)
- Endpoints novos (6 testes)
- **Total**: 40+ testes

## 6. Criterios de Aceitacao

- [ ] Geracao de material via LLM funcional
- [ ] Personalizacao de materiais existentes
- [ ] Trilhas de aprendizagem por condicao (DRC, DM2, HAS)
- [ ] Motor de recomendacao baseado em contexto
- [ ] Quiz de compreensao geravel via IA
- [ ] Progresso educativo persistido
- [ ] 6 endpoints novos funcionais
- [ ] 40+ testes
- [ ] Cobertura >= 85%

## 7. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~3 (api, config, docker)
- **Linhas estimadas**: ~1.500
- **Testes novos**: ~40
