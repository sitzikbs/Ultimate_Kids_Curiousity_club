"""Text-to-Speech service module."""

from services.tts.base import BaseTTSProvider
from services.tts.factory import TTSProviderFactory

__all__ = ["BaseTTSProvider", "TTSProviderFactory"]
