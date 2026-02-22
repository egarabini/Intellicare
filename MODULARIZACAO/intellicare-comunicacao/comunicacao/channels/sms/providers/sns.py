"""
Amazon SNS SMS Provider (D4).

Implementa provider SMS usando Amazon SNS.
"""

import logging
from typing import Dict, Any, Optional

import httpx

from comunicacao.channels.sms.config import SNSConfig
from comunicacao.channels.sms.providers.base import BaseSMSProvider

logger = logging.getLogger(__name__)


class SNSSMSProvider(BaseSMSProvider):
    """Provider SMS usando Amazon SNS."""

    def __init__(self, config: SNSConfig):
        """
        Inicializa provider SNS.

        Args:
            config: Configuração SNS.
        """
        self._config = config
        # Nota: Implementação simplificada sem boto3
        # Em produção, usar boto3.client('sns')
        logger.warning("SNS provider implementado de forma simplificada (sem boto3)")

    @property
    def provider_name(self) -> str:
        """Nome do provider."""
        return "sns"

    async def send(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia SMS via Amazon SNS.

        Args:
            to: Número do destinatário.
            text: Texto da mensagem.

        Returns:
            Dict: Resposta com message_id.

        Raises:
            NotImplementedError: Implementação simplificada.
        """
        # Validar número
        if not self.validate_phone_number(to):
            raise ValueError(f"Número inválido: {to}")

        # Truncar mensagem se necessário
        text = self.truncate_message(text)

        logger.info("Enviando SMS via SNS: to=%s", to)

        # TODO: Implementar com boto3
        # import boto3
        # sns = boto3.client('sns',
        #     aws_access_key_id=self._config.aws_access_key_id,
        #     aws_secret_access_key=self._config.aws_secret_access_key,
        #     region_name=self._config.aws_region
        # )
        # response = sns.publish(
        #     PhoneNumber=to,
        #     Message=text,
        #     MessageAttributes={
        #         'AWS.SNS.SMS.SMSType': {
        #             'DataType': 'String',
        #             'StringValue': 'Transactional'
        #         }
        #     }
        # )
        # return {
        #     "message_id": response['MessageId'],
        #     "status": "sent",
        #     "to": to,
        # }

        raise NotImplementedError("SNS provider requer boto3 (não instalado)")

    async def get_status(self, message_id: str) -> Optional[str]:
        """
        Consulta status de mensagem no SNS.

        Nota: SNS não tem endpoint de consulta de status.

        Args:
            message_id: ID da mensagem.

        Returns:
            Optional[str]: None (não suportado).
        """
        logger.warning("SNS não suporta consulta de status: %s", message_id)
        return None

    async def health_check(self) -> bool:
        """
        Verifica saúde do SNS.

        Returns:
            bool: True se credenciais estão configuradas.
        """
        # Verificação básica: credenciais configuradas
        if not self._config.aws_access_key_id or not self._config.aws_secret_access_key:
            logger.error("SNS health check falhou: credenciais não configuradas")
            return False

        logger.info("SNS health check: OK (credenciais configuradas)")
        return True

    async def close(self):
        """Fecha recursos (nenhum para SNS simplificado)."""
        pass

