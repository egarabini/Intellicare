"""
API Endpoints para Framingham Risk Score
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging

from nise.services.framingham import FraminghamCalculator, FraminghamInput, FraminghamOutput
from nise.services.oswaldo_client import OswaldoClient
from nise.api.endpoints.oswaldo import get_oswaldo_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/framingham", tags=["framingham"])


@router.post("/calcular", response_model=FraminghamOutput, status_code=status.HTTP_200_OK)
async def calcular_risco_framingham(
    input_data: FraminghamInput,
) -> FraminghamOutput:
    """
    Calcula risco cardiovascular Framingham
    
    **Inputs**:
    - sexo: M (Masculino) ou F (Feminino)
    - idade: 30-74 anos
    - colesterol_total: 100-400 mg/dL
    - hdl: 20-100 mg/dL
    - pa_sistolica: 90-200 mmHg
    - tabagismo: true/false
    - diabetes: true/false
    
    **Output**:
    - risco_10_anos: Risco em % (0-100)
    - classificacao: baixo (<10%), intermediario (10-20%), alto (>20%)
    - pontos_totais: Pontos calculados
    - recomendacoes: Lista de recomendações clínicas
    - Detalhamento de pontos por fator
    
    **Exemplo**:
    ```json
    {
        "sexo": "M",
        "idade": 55,
        "colesterol_total": 220,
        "hdl": 45,
        "pa_sistolica": 140,
        "tabagismo": true,
        "diabetes": false
    }
    ```
    """
    try:
        logger.info(f"Calculando risco Framingham para paciente: sexo={input_data.sexo}, idade={input_data.idade}")
        
        # Calcular risco
        resultado = FraminghamCalculator.calcular(input_data)
        
        logger.info(
            f"Risco calculado: {resultado.risco_10_anos}% "
            f"(classificacao={resultado.classificacao}, pontos={resultado.pontos_totais})"
        )
        
        return resultado
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de validação: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erro ao calcular risco Framingham: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular risco"
        )


@router.get("/paciente/{paciente_id}", response_model=FraminghamOutput, status_code=status.HTTP_200_OK)
async def calcular_risco_paciente(
    paciente_id: str,
    oswaldo: OswaldoClient = Depends(get_oswaldo_client),
) -> FraminghamOutput:
    """
    Calcula risco Framingham para paciente do Oswaldo
    
    Busca dados do paciente no Oswaldo e calcula risco automaticamente.
    
    **Parâmetros**:
    - paciente_id: ID do paciente no Oswaldo
    
    **Dados necessários no Oswaldo**:
    - Dados demográficos (sexo, idade)
    - Última medição de PA sistólica
    - Último lipidograma (colesterol total, HDL)
    - Histórico de tabagismo
    - Diagnóstico de diabetes
    
    **Retorna**:
    - FraminghamOutput com risco calculado
    
    **Erros**:
    - 404: Paciente não encontrado
    - 400: Dados insuficientes para cálculo
    - 500: Erro interno
    """
    try:
        logger.info(f"Buscando dados do paciente {paciente_id} no Oswaldo")
        
        # Buscar resumo do paciente
        resumo = await oswaldo.get_paciente_resumo(paciente_id)
        
        if not resumo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente {paciente_id} não encontrado"
            )
        
        # Extrair dados necessários
        try:
            # Sexo e idade
            sexo = resumo.get("sexo")
            idade = resumo.get("idade")
            
            if not sexo or not idade:
                raise ValueError("Sexo ou idade não disponíveis")
            
            # Última PA sistólica
            pa_sistolica = resumo.get("ultima_pa_sistolica")
            if not pa_sistolica:
                raise ValueError("Pressão arterial sistólica não disponível")
            
            # Último lipidograma
            lipidograma = resumo.get("ultimo_lipidograma", {})
            colesterol_total = lipidograma.get("colesterol_total")
            hdl = lipidograma.get("hdl")
            
            if not colesterol_total or not hdl:
                raise ValueError("Lipidograma (colesterol total e HDL) não disponível")
            
            # Tabagismo
            tabagismo = resumo.get("tabagismo", False)
            
            # Diabetes
            diabetes = resumo.get("tem_diabetes", False)
            
        except (KeyError, ValueError) as e:
            logger.error(f"Dados insuficientes para cálculo: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dados insuficientes para cálculo de risco: {str(e)}"
            )
        
        # Criar input
        input_data = FraminghamInput(
            sexo=sexo,
            idade=idade,
            colesterol_total=colesterol_total,
            hdl=hdl,
            pa_sistolica=pa_sistolica,
            tabagismo=tabagismo,
            diabetes=diabetes,
        )
        
        # Calcular risco
        resultado = FraminghamCalculator.calcular(input_data)
        
        logger.info(
            f"Risco calculado para paciente {paciente_id}: {resultado.risco_10_anos}% "
            f"(classificacao={resultado.classificacao})"
        )
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular risco para paciente {paciente_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular risco"
        )

