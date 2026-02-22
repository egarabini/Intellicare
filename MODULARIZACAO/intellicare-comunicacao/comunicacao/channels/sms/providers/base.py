"""
Base provider para SMS (D4).

Define interface abstrata para providers SMS.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSMSProvider(ABC):
    """Interface abstrata para providers SMS."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Nome do provider.

        Returns:
            str: Nome do provider.
        """
        pass

    @abstractmethod
    async def send(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia SMS.

        Args:
            to: Número do destinatário (+55...).
            text: Texto da mensagem.

        Returns:
            Dict: Resposta do provider com message_id.

        Raises:
            Exception: Se erro no envio.
        """
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> Optional[str]:
        """
        Consulta status de mensagem.

        Args:
            message_id: ID da mensagem no provider.

        Returns:
            Optional[str]: Status ("sent", "delivered", "failed") ou None.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica saúde do provider.

        Returns:
            bool: True se provider está disponível.
        """
        pass

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Valida formato de número de telefone.

        Args:
            phone_number: Número a validar.

        Returns:
            bool: True se válido.
        """
        # Validação básica: deve começar com + e ter pelo menos 10 dígitos
        if not phone_number.startswith("+"):
            return False

        # Remover + e verificar se resto são dígitos
        digits = phone_number[1:]
        if not digits.isdigit():
            return False

        # Mínimo 10 dígitos (código país + número)
        if len(digits) < 10:
            return False

        return True

    def truncate_message(self, text: str, max_length: int = 160) -> str:
        """
        Trunca mensagem se exceder limite.

        Args:
            text: Texto original.
            max_length: Tamanho máximo.

        Returns:
            str: Texto truncado.
        """
        if len(text) <= max_length:
            return text

        # Truncar e adicionar ...
        return text[: max_length - 3] + "..."

