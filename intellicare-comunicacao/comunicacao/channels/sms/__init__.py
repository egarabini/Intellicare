"""
SMS - D4.

Implementa dispatcher para SMS via múltiplos providers:
- Twilio
- Zenvia
- Amazon SNS

Usado como fallback quando WhatsApp não disponível.
"""

from comunicacao.channels.sms.config import SMSConfig, TwilioConfig, ZenviaConfig, SNSConfig
from comunicacao.channels.sms.dispatcher import SMSDispatcher
from comunicacao.channels.sms.models import (
    SMSMessage,
    SMSSendRequest,
    SMSSendResponse,
    SMSStatusUpdate,
)
from comunicacao.channels.sms.providers import (
    BaseSMSProvider,
    TwilioSMSProvider,
    ZenviaSMSProvider,
    SNSSMSProvider,
)

__all__ = [
    "SMSConfig",
    "TwilioConfig",
    "ZenviaConfig",
    "SNSConfig",
    "SMSDispatcher",
    "SMSMessage",
    "SMSSendRequest",
    "SMSSendResponse",
    "SMSStatusUpdate",
    "BaseSMSProvider",
    "TwilioSMSProvider",
    "ZenviaSMSProvider",
    "SNSSMSProvider",
]

