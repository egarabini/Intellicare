"""Simplificador de linguagem médica para leigos."""

import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from geralda.ai.language.medical_glossary import MEDICAL_GLOSSARY, simplify_term


logger = logging.getLogger(__name__)


# Níveis de leitura
READING_LEVELS = {
    "basico": "Fundamental incompleto - Frases curtas, sem termos técnicos",
    "intermediario": "Fundamental completo/Médio - Termos simples com explicação",
    "avancado": "Superior - Termos técnicos com explicação detalhada",
}


class MedicalSimplifier:
    """
    Motor de simplificação de linguagem médica.

    Usa glossário + LLM (se disponível) para traduzir termos médicos
    em linguagem acessível para pacientes.
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        """
        Inicializa simplificador.

        Args:
            llm: Instância de LLM (opcional, para fallback inteligente)
        """
        self._llm = llm
        self._glossary = MEDICAL_GLOSSARY

    def simplify_term(self, term: str) -> str:
        """
        Traduz termo médico usando glossário.

        Args:
            term: Termo médico

        Returns:
            Tradução em linguagem leiga
        """
        return simplify_term(term)

    async def simplify_text(
        self,
        text: str,
        level: str = "basico",
    ) -> str:
        """
        Simplifica texto completo para o nível especificado.

        Args:
            text: Texto original
            level: Nível de leitura ("basico", "intermediario", "avancado")

        Returns:
            Texto simplificado
        """
        if not text:
            return ""

        # Primeiro: substituir termos do glossário
        simplified = self._apply_glossary(text)

        # Segundo: se tiver LLM, refinar com IA
        if self._llm:
            simplified = await self._refine_with_llm(simplified, level)

        return simplified

    def _apply_glossary(self, text: str) -> str:
        """
        Aplica glossário ao texto, substituindo termos médicos.

        Args:
            text: Texto original

        Returns:
            Texto com termos substituídos
        """
        result = text

        # Ordenar por tamanho (descendente) para substituir termos mais longos primeiro
        for term in sorted(self._glossary.keys(), key=len, reverse=True):
            if term.lower() in result.lower():
                # Substituir preservando caixa quando possível
                result = result.replace(term, self._glossary[term])

        return result

    async def _refine_with_llm(self, text: str, level: str) -> str:
        """
        Usa LLM para refinar texto conforme nível de leitura.

        Args:
            text: Texto já processado pelo glossário
            level: Nível de leitura

        Returns:
            Texto refinado pelo LLM
        """
        prompt = self._build_simplification_prompt(text, level)

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.warning(f"LLM refinement failed: {e}")
            return text

    def _build_simplification_prompt(self, text: str, level: str) -> str:
        """
        Constrói prompt para simplificação com LLM.

        Args:
            text: Texto a simplificar
            level: Nível de leitura

        Returns:
            Prompt formatado
        """
        if level == "basico":
            instructions = """
- Use frases curtas (máximo 15 palavras)
- Evite palavras difíceis
- Use comparações do dia a dia
- Exemplo: "taxa de filtração reduzida" -> "os rins estão filtrando menos do que deveriam"
"""
        elif level == "intermediario":
            instructions = """
- Use frases moderadas (máximo 25 palavras)
- Pode mencionar nomes de exames, mas explique o que são
- Exemplo: "hemoglobina glicada de 8.5%" -> "a hemoglobina glicada (exame que mede o açúcar médio) está em 8.5%, acima do ideal"
"""
        else:  # avancado
            instructions = """
- Pode usar termos técnicos, mas explique o significado
- Mantenha precisão clínica
- Exemplo: "TFG de 38 mL/min/1.73m²" -> "taxa de filtração glomerular de 38 mL/min/1.73m² (capacidade dos rins de filtrar o sangue, está reduzida)"
"""

        return f"""Você é especialista em comunicação acessível em saúde.

TAREFA: Reescreva o texto abaixo em linguagem {level.upper()}.

{instructions}

TEXTO ORIGINAL:
{text}

TEXTO SIMPLIFICADO:
"""

    async def explain_condition(
        self,
        condition_code: str,
        condition_name: Optional[str] = None,
        level: str = "basico",
    ) -> str:
        """
        Gera explicação de uma condição em linguagem acessível.

        Args:
            condition_code: Código da condição (ex: "I10", "E11")
            condition_name: Nome da condição (opcional)
            level: Nível de leitura

        Returns:
            Explicação em linguagem acessível
        """
        if not self._llm:
            # Sem LLM: usa glossário + template simples
            name = condition_name or condition_code
            simplified = self.simplify_term(name)
            return f"{simplified}. Entre em contato com sua equipe para saber mais."

        prompt = f"""Explique a condição {condition_code} ({condition_name or ''}) em linguagem {level}.

Nível: {READING_LEVELS.get(level, level)}

Forneça:
1. O que é (em linguagem simples)
2. Quais os sintomas principais
3. Como é o tratamento
4. O que o paciente pode fazer para se cuidar

Use tom acolhedor e motivador. Máximo 200 palavras.
"""

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Error explaining condition: {e}")
            return f"Condição: {condition_code}. Entre em contato com sua equipe de saúde para explicações."

    async def explain_medication(
        self,
        medication_name: str,
        level: str = "basico",
    ) -> str:
        """
        Explica um medicamento em linguagem simples.

        Args:
            medication_name: Nome do medicamento
            level: Nível de leitura

        Returns:
            Explicação em linguagem acessível
        """
        simplified_name = self.simplify_term(medication_name)

        if not self._llm:
            return f"""{simplified_name}

- Para que serve: consulte seu médico
- Como tomar: siga a prescrição médica
- Cuidados: tome no horário certo"""

        prompt = f"""Explique o medicamento {medication_name} ({simplified_name}) em linguagem {level}.

Forneça:
1. Para que serve (em linguagem simples)
2. Como tomar (horários, com ou sem comida)
3. Cuidados importantes
4. O que fazer se esquecer uma dose

Máximo 150 palavras.
"""

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Error explaining medication: {e}")
            return f"""{simplified_name}

Entre em contato com sua equipe de saúde para instruções."""

    async def explain_exam_result(
        self,
        exam: str,
        value: float,
        unit: str,
        reference_min: Optional[float] = None,
        reference_max: Optional[float] = None,
        level: str = "basico",
    ) -> str:
        """
        Explica resultado de exame em linguagem simples.

        Args:
            exam: Nome do exame
            value: Valor obtido
            unit: Unidade de medida
            reference_min: Valor mínimo de referência
            reference_max: Valor máximo de referência
            level: Nível de leitura

        Returns:
            Explicação em linguagem acessível
        """
        simplified_exam = self.simplify_term(exam)

        if reference_min is not None and reference_max is not None:
            in_range = reference_min <= value <= reference_max
            status = "normal" if in_range else "fora do normal"
        else:
            status = "sem referência"

        if not self._llm:
            return f"""{simplified_exam}: {value} {unit} ({status})
{"Está dentro do normal." if status == "normal" else "Entre em contato com sua equipe para explicar o resultado."}"""

        prompt = f"""Explique o resultado de exame abaixo em linguagem {level}.

Exame: {simplified_exam}
Resultado: {value} {unit}
Referência: {reference_min or '?'} a {reference_max or '?'}
Status: {status}

Forneça:
1. O que esse exame mede
2. O que o resultado significa
3. Se está normal ou não (e por quê)
4. O que fazer a seguir

Máximo 150 palavras.
"""

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Error explaining exam result: {e}")
            return f"""{simplified_exam}: {value} {unit}
Entre em contato com sua equipe de saúde para explicações."""
