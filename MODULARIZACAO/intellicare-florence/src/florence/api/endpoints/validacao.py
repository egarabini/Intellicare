"""
Endpoint: Validação Clínica
===========================

Endpoints para testar e validar exames clínicos usando os 6 validadores
implementados em ClinicaAlgorithmValidator.

Uso:
    POST /api/v1/validacao/validador-clinico
    POST /api/v1/validacao/tipos-suportados
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Adicionar src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from florence.services.clinical_validation import ClinicaAlgorithmValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/validacao", tags=["validacao"])


class SolicitacaoValidacao(BaseModel):
    """Solicitação de validação de exame clínico"""
    
    tipo_exame: str = Field(
        ...,
        description="Tipo de exame: hemograma, lipidograma, hepatograma, funcao_renal, glicemia, exame_completo"
    )
    dados: Dict[str, Any] = Field(
        ...,
        description="Dicionário com parâmetros do exame"
    )
    sexo: Optional[str] = Field(
        None,
        description="Sexo do paciente: M ou F (necessário para alguns validadores)"
    )
    age_anos: Optional[int] = Field(
        None,
        description="Idade do paciente em anos (necessário para função renal)"
    )
    paciente_diabetico: Optional[bool] = Field(
        False,
        description="Se paciente é diabético (necessário para glicemia)"
    )
    tipo_amostra: Optional[str] = Field(
        "aleatoria",
        description="Tipo de amostra para glicemia: jejum, aleatoria, pos_prandial"
    )


class DetalheValidacao(BaseModel):
    """Detalhe de um problema encontrado na validação"""
    
    parametro: str
    valor_reportado: Any
    valor_esperado_min: Optional[float] = None
    valor_esperado_max: Optional[float] = None
    severidade: str  # info, aviso, critica
    mensagem: str


class RespostaValidacao(BaseModel):
    """Resposta de validação clínica"""
    
    valido: bool
    tipo_exame: str
    mensagem: str
    detalhes: Optional[List[DetalheValidacao]] = None


@router.post(
    "/validador-clinico",
    response_model=RespostaValidacao,
    summary="Validar Exame Clínico",
    description="Testa um exame clínico contra validadores correspondentes"
)
def validar_exame(solicitacao: SolicitacaoValidacao) -> RespostaValidacao:
    """
    Endpoint para validar exames clínicos usando os 6 validadores implementados.

    **Exemplo de uso para Hemograma**:
    ```json
    {
        "tipo_exame": "hemograma",
        "sexo": "M",
        "dados": {
            "hemoglobina": 14.5,
            "hematocrito": 42.5,
            "plaquetas": 250,
            "leucocitos": 7.0,
            "diferenciais": {
                "neutrofilos": 60,
                "linfocitos": 30,
                "monocitos": 8,
                "eosinofilos": 2
            }
        }
    }
    ```

    **Resposta esperada**:
    ```json
    {
        "valido": true,
        "tipo_exame": "hemograma",
        "mensagem": "Hemograma válido",
        "detalhes": null
    }
    ```

    **Tipos de exame suportados**:
    - hemograma
    - lipidograma
    - hepatograma
    - funcao_renal
    - glicemia
    - exame_completo

    **Campos obrigatórios por tipo**:

    **Hemograma**:
    - hemoglobina, hematocrito, plaquetas, leucocitos, diferenciais, sexo

    **Lipidograma**:
    - colesterol_total, triglicerida, hdl, ldl

    **Hepatograma**:
    - ast, alt, bilirrubina_total, bilirrubina_direta, fosfatase_alcalina

    **Função Renal**:
    - creatinina, ureia, age_anos

    **Glicemia**:
    - glicemia, tipo_amostra, paciente_diabetico

    **Exame Completo**:
    - Um ou mais dos acima + sexo, age_anos
    """

    tipo = solicitacao.tipo_exame.lower().strip()
    validador = ClinicaAlgorithmValidator

    try:
        # HEMOGRAMA
        if tipo == "hemograma":
            hemoglobina = solicitacao.dados.get("hemoglobina")
            hematocrito = solicitacao.dados.get("hematocrito")
            plaquetas = solicitacao.dados.get("plaquetas")
            # Aceitar ambas formas: leucocitos ou leucócitos
            leucocitos = solicitacao.dados.get("leucocitos") or solicitacao.dados.get("leucócitos")
            diferenciais = solicitacao.dados.get("diferenciais", {})
            sexo = solicitacao.sexo or "M"

            if not all([hemoglobina, hematocrito, plaquetas, leucocitos]):
                raise ValueError(
                    "Hemograma requer: hemoglobina, hematocrito, plaquetas, leucocitos"
                )

            valido, msg = validador.validar_hemograma(
                hemoglobina=hemoglobina,
                hematocrito=hematocrito,
                plaquetas=plaquetas,
                leucócitos=leucocitos,
                diferenciais=diferenciais,
                sexo=sexo
            )

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        # LIPIDOGRAMA
        elif tipo == "lipidograma":
            colesterol_total = solicitacao.dados.get("colesterol_total")
            # Aceitar ambas: triglicerida ou triglicérides
            triglicerida = solicitacao.dados.get("triglicerida") or solicitacao.dados.get("triglicérides")
            hdl = solicitacao.dados.get("hdl")
            ldl = solicitacao.dados.get("ldl")

            if not all([colesterol_total, triglicerida, hdl, ldl]):
                raise ValueError(
                    "Lipidograma requer: colesterol_total, triglicerida, hdl, ldl"
                )

            valido, msg = validador.validar_lipidograma(
                colesterol_total=colesterol_total,
                triglicérides=triglicerida,
                hdl=hdl,
                ldl=ldl
            )

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        # HEPATOGRAMA
        elif tipo == "hepatograma":
            ast = solicitacao.dados.get("ast")
            alt = solicitacao.dados.get("alt")
            bilirrubina_total = solicitacao.dados.get("bilirrubina_total")
            bilirrubina_direta = solicitacao.dados.get("bilirrubina_direta")
            fosfatase_alcalina = solicitacao.dados.get("fosfatase_alcalina")

            if not all([ast, alt, bilirrubina_total, bilirrubina_direta, fosfatase_alcalina]):
                raise ValueError(
                    "Hepatograma requer: ast, alt, bilirrubina_total, bilirrubina_direta, fosfatase_alcalina"
                )

            valido, msg = validador.validar_hepatograma(
                ast=ast,
                alt=alt,
                bilirrubina_total=bilirrubina_total,
                bilirrubina_direta=bilirrubina_direta,
                fosfatase_alcalina=fosfatase_alcalina
            )

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        # FUNÇÃO RENAL
        elif tipo == "funcao_renal":
            creatinina = solicitacao.dados.get("creatinina")
            ureia = solicitacao.dados.get("ureia")
            age_anos = solicitacao.age_anos

            if not all([creatinina, ureia, age_anos]):
                raise ValueError(
                    "Função Renal requer: creatinina, ureia, age_anos"
                )

            valido, msg = validador.validar_funcao_renal(
                creatinina=creatinina,
                ureia=ureia,
                idade=age_anos
            )

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        # GLICEMIA
        elif tipo == "glicemia":
            glicemia = solicitacao.dados.get("glicemia")
            tipo_amostra = solicitacao.tipo_amostra or "aleatoria"
            paciente_diabetico = solicitacao.paciente_diabetico or False

            if not glicemia:
                raise ValueError("Glicemia requer: glicemia")

            valido, msg = validador.validar_glicemia(
                glicemia=glicemia,
                tipo_amostra=tipo_amostra,
                paciente_diabetico=paciente_diabetico
            )

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        # EXAME COMPLETO
        elif tipo == "exame_completo":
            sexo = solicitacao.sexo or "M"
            age_anos = solicitacao.age_anos

            valido, resultado = validador.validar_exame_completo(
                exame_data=solicitacao.dados,
                sexo=sexo,
                idade=age_anos
            )

            msg = "Exame completo processado"
            if valido:
                msg = "Exame completo válido ✅"
            else:
                erros = resultado.get("erros", [])
                avisos = resultado.get("avisos", [])
                if erros:
                    msg = f"Exame com problemas: {', '.join(erros[:2])}"
                elif avisos:
                    msg = f"Exame com aviso: {', '.join(avisos[:1])}"

            return RespostaValidacao(
                valido=valido,
                tipo_exame=tipo,
                mensagem=msg,
                detalhes=None
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de exame '{tipo}' não suportado. Use: hemograma, lipidograma, hepatograma, funcao_renal, glicemia, exame_completo"
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao validar exame: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get(
    "/tipos-suportados",
    summary="Tipos de Exame Suportados",
    description="Lista todos os tipos de exame que podem ser validados"
)
def tipos_validadores_suportados():
    """
    Retorna lista de tipos de exame suportados pela plataforma Florence.

    **Resposta**:
    ```json
    {
        "tipos": [
            "hemograma",
            "lipidograma",
            "hepatograma",
            "funcao_renal",
            "glicemia",
            "exame_completo"
        ],
        "total": 6
    }
    ```
    """
    return {
        "tipos": [
            "hemograma",
            "lipidograma",
            "hepatograma",
            "funcao_renal",
            "glicemia",
            "exame_completo"
        ],
        "total": 6,
        "descricoes": {
            "hemograma": "Hematócrito, hemoglobina, leucócitos e diferencial",
            "lipidograma": "Colesterol total, HDL, LDL, triglicerida (Friedewald)",
            "hepatograma": "AST, ALT, bilirrubina total/direta, fosfatase alcalina",
            "funcao_renal": "Creatinina, ureia e razão ureia/creatinina",
            "glicemia": "Glicose no sangue com contexto de coleta",
            "exame_completo": "Agregação de todos os validadores acima"
        }
    }


@router.get(
    "/saude",
    summary="Health Check",
    description="Verifica se a API está operacional"
)
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "validadores_disponiveis": 6,
        "versao": "1.0.0"
    }
