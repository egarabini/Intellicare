from typing import Dict
import logging

class LGPDComplianceGateway:
    """
    Gateway de conformidade LGPD: audita e filtra eventos sensíveis.
    """
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logging.getLogger("lgpd")

    def audit_event(self, event: Dict, action: str = "access"):
        if self.enabled:
            self.logger.info(f"LGPD AUDIT | action={action} | event={event}")

    def filter_sensitive(self, data: Dict) -> Dict:
        # Exemplo: remove campos sensíveis
        filtered = {k: v for k, v in data.items() if k not in ("cpf", "email", "phone")}
        return filtered
