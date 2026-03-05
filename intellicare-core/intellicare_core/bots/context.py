"""
Bot Execution Context for IntelliCare.
Encapsulates all the contextual data needed by a Bot to execute its task.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from .client import IntelliCareClient

@dataclass
class EventMetadata:
    """Metadata about the event that triggered the bot."""
    subscription_id: Optional[str] = None
    interaction: Optional[str] = None
    trigger_type: str = "subscription"

class BotLogger:
    """Captures all print statements outputted by the bot."""
    def __init__(self):
        self._logs = []

    def info(self, *args, **kwargs):
        """Standard print captured locally."""
        message = " ".join(str(a) for a in args)
        self._logs.append(message)

    def get_log_output(self) -> str:
        """Returns the accumulated logs joined by newlines."""
        return "\n".join(self._logs)

@dataclass
class BotExecutionContext:
    """Context passed to the RestrictedPython script namespace."""
    input_resource: Dict[str, Any]
    fhir_client: IntelliCareClient
    secrets: Dict[str, str]
    event_metadata: EventMetadata
    logger: BotLogger
