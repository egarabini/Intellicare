"""HL7v2 Message Handlers.

This module contains handlers for different HL7v2 message types.
Each handler is responsible for:
1. Parsing the raw HL7v2 message
2. Validating message structure and required fields
3. Converting to FHIR resources
4. Publishing events
5. Generating ACK responses
"""

from .adt_a04 import ADTA04Handler

__all__ = ["ADTA04Handler"]

