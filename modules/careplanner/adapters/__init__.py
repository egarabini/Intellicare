"""Adapters de integracao do CarePlanner."""

from .jitsi import JitsiAdapter
from .kestra import KestraAdapter
from .rocketchat import RocketChatAdapter

__all__ = ["JitsiAdapter", "KestraAdapter", "RocketChatAdapter"]
