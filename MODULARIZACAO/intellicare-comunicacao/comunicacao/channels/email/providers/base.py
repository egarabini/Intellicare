from abc import ABC, abstractmethod
from ..models import EmailMessage
from typing import Dict, Any

class BaseEmailProvider(ABC):
    """Abstract base class for Email providers."""
    
    @abstractmethod
    def send(self, message: EmailMessage) -> bool:
        """Sends an email message. Returns True if successful."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Checks the health of the provider."""
        pass
