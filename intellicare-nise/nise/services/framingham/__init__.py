"""
Framingham Risk Score Calculator

Calcula risco cardiovascular em 10 anos baseado no algoritmo Framingham.
"""

from .calculator import FraminghamCalculator
from .models import FraminghamInput, FraminghamOutput

__all__ = ["FraminghamCalculator", "FraminghamInput", "FraminghamOutput"]

