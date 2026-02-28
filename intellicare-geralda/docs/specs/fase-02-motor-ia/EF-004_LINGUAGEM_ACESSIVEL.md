# EF-004 — Linguagem Acessivel

> Simplificacao de linguagem medica para comunicacao com pacientes de diferentes niveis de letramento.

## 1. Objetivo

Toda comunicacao da Geralda com pacientes deve ser em linguagem acessivel. O motor de IA deve:
- Traduzir termos medicos para linguagem cotidiana
- Adaptar o nivel de complexidade ao perfil do paciente
- Manter a precisao clinica mesmo na simplificacao
- Gerar explicacoes em diferentes formatos (texto curto, texto longo, topicos)

## 2. Justificativa

- **Adesao**: Paciente que entende o tratamento adere mais
- **Equidade**: Atender pacientes de todos os niveis de escolaridade
- **Seguranca**: Evitar mal-entendidos sobre medicamentos e cuidados
- **Humanizacao**: Comunicacao acolhedora e respeitosa

## 3. Escopo

### 3.1 Motor de Simplificacao

Criar `geralda/ai/language/` com:

```
geralda/ai/language/
  __init__.py
  simplifier.py          # Motor principal de simplificacao
  medical_glossary.py    # Dicionario termos medicos -> leigo
  reading_level.py       # Classificador de nivel de leitura
  formatter.py           # Formatador por tipo de output
```

### 3.2 Glossario Medico-Leigo

Dicionario de termos medicos mapeados para linguagem simples:

```python
MEDICAL_GLOSSARY = {
    # Condicoes
    "hipertensao arterial": "pressao alta",
    "diabetes mellitus tipo 2": "diabetes tipo 2 (acucar alto no sangue)",
    "doenca renal cronica": "problema nos rins (eles filtram menos)",
    "insuficiencia cardiaca": "coracao fraco (nao bombeia direito)",
    "dislipidemia": "colesterol ou triglicerides alto",
    "nefropatia diabetica": "dano nos rins causado pelo diabetes",
    "neuropatia periferica": "dor ou dormencia nos pes e maos",

    # Exames
    "taxa de filtracao glomerular": "capacidade dos rins de filtrar o sangue",
    "hemoglobina glicada": "media do acucar no sangue nos ultimos 3 meses",
    "creatinina serica": "substancia que mostra como os rins estao funcionando",
    "albuminuria": "proteina na urina (sinal de problema nos rins)",
    "perfil lipidico": "exame de colesterol e gorduras no sangue",

    # Medicamentos
    "anti-hipertensivo": "remedio para baixar a pressao",
    "hipoglicemiante oral": "remedio para baixar o acucar no sangue",
    "inibidor de ECA": "remedio que protege o coracao e os rins",
    "diuretico": "remedio que ajuda a eliminar liquido pela urina",
    "estatina": "remedio para baixar o colesterol",

    # Procedimentos
    "aferir pressao arterial": "medir a pressao",
    "glicemia capilar": "furar o dedo para ver o acucar no sangue",
    "eletrocardiograma": "exame que ve o ritmo do coracao",

    # Resultados
    "dentro dos valores de referencia": "resultado normal",
    "acima do valor de referencia": "resultado acima do normal",
    "tendencia de piora": "os numeros estao piorando com o tempo",
    "estagio 3a": "nivel moderado de comprometimento",
}
```

### 3.3 Niveis de Leitura

| Nivel | Descricao | Caracteristicas |
|-------|-----------|-----------------|
| `basico` | Fundamental incompleto | Frases curtas, sem termos tecnicos, analogias do cotidiano |
| `intermediario` | Fundamental completo / Medio | Termos simples, explicacoes breves, pode mencionar nomes de exames |
| `avancado` | Superior ou profissional de saude | Termos tecnicos com explicacao, referencias a guidelines |

### 3.4 Perfil de Comunicacao do Paciente

Armazenar na tabela `care_plans` (ou nova tabela `patient_preferences`):

```sql
CREATE TABLE patient_preferences (
    patient_id VARCHAR(64) PRIMARY KEY,
    reading_level VARCHAR(20) DEFAULT 'basico',
    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
    preferred_format VARCHAR(20) DEFAULT 'short',   -- short, long, topics
    preferred_channel VARCHAR(20) DEFAULT 'app',     -- app, sms, whatsapp
    accessibility_needs JSONB,                       -- ex: {"large_text": true}
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### 3.5 Funcoes do Simplifier

```python
class MedicalSimplifier:
    def __init__(self, llm: Optional[BaseChatModel], glossary: dict):
        self._llm = llm
        self._glossary = glossary

    def simplify_term(self, term: str) -> str:
        """Busca no glossario. Se nao encontrar, usa LLM."""

    async def simplify_text(self, text: str, level: str = "basico") -> str:
        """Simplifica texto completo para o nivel especificado."""

    async def explain_condition(self, condition_code: str, level: str = "basico") -> str:
        """Gera explicacao de uma condicao em linguagem acessivel."""

    async def explain_medication(self, medication: str, level: str = "basico") -> str:
        """Explica um medicamento (para que serve, como tomar, cuidados)."""

    async def explain_exam_result(self, exam: str, value: float, unit: str, reference: str, level: str = "basico") -> str:
        """Explica resultado de exame em linguagem simples."""

    async def generate_care_summary(self, plan: CarePlan, level: str = "basico") -> str:
        """Gera resumo do plano de cuidado para o paciente."""
```

### 3.6 Prompts de Simplificacao

```python
SIMPLIFY_TEXT_PROMPT = """
Voce e a Geralda, especialista em comunicacao acessivel em saude.

TAREFA: Reescreva o texto abaixo em linguagem {level}.

REGRAS PARA NIVEL "basico":
- Use frases curtas (maximo 15 palavras)
- Evite palavras dificeis
- Use comparacoes do dia a dia
- Exemplo: "taxa de filtracao glomerular reduzida" -> "os rins estao filtrando menos do que deveriam"

REGRAS PARA NIVEL "intermediario":
- Use frases moderadas (maximo 25 palavras)
- Pode mencionar nomes de exames, mas explique o que sao
- Exemplo: "hemoglobina glicada de 8.5%" -> "a hemoglobina glicada (exame que mede o acucar medio) esta em 8.5%, acima do ideal"

TEXTO ORIGINAL:
{original_text}

TEXTO SIMPLIFICADO:
"""
```

### 3.7 Formatador de Saida

```python
class OutputFormatter:
    def format_short(self, text: str) -> str:
        """Formato curto para mensagens (max 280 chars)"""

    def format_long(self, text: str) -> str:
        """Formato longo para educacao"""

    def format_topics(self, text: str) -> list[str]:
        """Formato em topicos numerados"""

    def format_reminder(self, task: CareTask, level: str) -> str:
        """Formata lembrete de tarefa em linguagem acessivel"""
```

## 4. Exemplos de Transformacao

### Exemplo 1: Resultado de Exame
**Original (profissional)**:
> Creatinina serica 2.1 mg/dL. eGFR estimada 38 mL/min/1.73m2. Classificacao KDIGO G3b/A2.

**Basico**:
> Seu exame dos rins mostrou que eles estao trabalhando menos do que deveriam. Funciona assim: os rins filtram o sangue, e agora eles estao filtrando so 38% do normal. E importante continuar o tratamento certinho.

**Intermediario**:
> A creatinina esta em 2.1 (o normal e ate 1.2). Isso mostra que seus rins estao com a filtracao reduzida (38 mL/min). Pela classificacao medica, esta no estagio 3b, que e moderado-grave. O acompanhamento regular e essencial.

### Exemplo 2: Lembrete de Medicamento
**Original**: Administrar Losartana Potassica 50mg via oral 1x/dia em jejum
**Basico**: Tome 1 comprimido de Losartana todo dia de manha, antes de comer.
**Intermediario**: Tome Losartana 50mg uma vez ao dia, preferencialmente em jejum pela manha.

## 5. Testes

- Glossario: lookup de 20+ termos (20 testes)
- Simplifier com LLM mockado: cada nivel (9 testes)
- Formatter: cada formato (6 testes)
- Integracao com endpoint de educacao (5 testes)
- **Total**: 40+ testes

## 6. Criterios de Aceitacao

- [ ] Glossario medico-leigo com 50+ termos mapeados
- [ ] Simplificacao funcional em 3 niveis (basico, intermediario, avancado)
- [ ] Perfil de preferencia do paciente persistido
- [ ] Formatacao em 3 formatos (curto, longo, topicos)
- [ ] Funciona sem LLM (fallback para glossario puro)
- [ ] 40+ testes
- [ ] Cobertura >= 90%

## 7. Estimativa de Complexidade

- **Arquivos novos**: ~6
- **Arquivos modificados**: ~3
- **Linhas estimadas**: ~1.000
- **Testes novos**: ~40
