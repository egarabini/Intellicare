"""HL7v2 Agent — Parser, converters, and message handlers.

This module implements HL7v2 message parsing and conversion to FHIR R4 resources.
Supports ADT (Admit/Discharge/Transfer) messages from Brazilian hospital systems.

Key components:
- parser.py: Core HL7v2 parser (pipe-delimited format)
- segments/: MSH, PID, PV1 segment parsers
- messages/: Message handlers (ADT^A04, etc.)
- converters/: HL7v2 → FHIR converters
- ack.py: ACK message generator
- validators.py: HL7v2 validation

Supported HL7v2 versions: 2.5, 2.5.1, 2.6
Supported encodings: UTF-8, ISO-8859-1 (Brazilian legacy systems)
"""

from .parser import HL7v2Parser

__all__ = ["HL7v2Parser"]

