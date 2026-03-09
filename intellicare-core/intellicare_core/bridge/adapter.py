"""BaseHISAdapter — contrato que todo adaptador HIS deve implementar."""

from abc import ABC, abstractmethod
from typing import Any

from intellicare_core.bridge.context import HISContext


class BaseHISAdapter(ABC):
    """Contrato que todo adaptador HIS deve implementar.

    Cada HIS (Tasy, Feegow, MV...) implementa esta classe em intellicare-bridge,
    traduzindo a API proprietária para FHIR R4 Bundle.
    """

    @property
    @abstractmethod
    def his_system(self) -> str:
        """Identificador do sistema (ex: 'feegow'). Deve coincidir com HISSystem enum."""
        ...

    @abstractmethod
    async def resolve_launch_context(self, launch_token: str, iss: str) -> HISContext:
        """Resolve o launch token do EHR Launch em HISContext completo.

        Chamado pelo GRAHAME quando recebe GET /smart/launch com parâmetros do HIS.
        """
        ...

    @abstractmethod
    async def get_patient_bundle(self, context: HISContext) -> dict[str, Any]:
        """Retorna FHIR Bundle com dados do paciente traduzidos da API do HIS.

        Bundle deve conter: Patient, Condition[], Observation[], MedicationRequest[].
        Tipo: transaction (para ingestão via $process-message).
        """
        ...

    @abstractmethod
    async def push_cds_card(self, context: HISContext, card: dict[str, Any]) -> bool:
        """Envia um CDS Hook card de volta para o HIS (se o HIS suportar write-back).

        Retorna True se o HIS aceitou o card, False caso contrário.
        """
        ...

    async def validate_connection(self) -> bool:
        """Testa conectividade básica com o HIS. Default: False (sem conexão real)."""
        return False
