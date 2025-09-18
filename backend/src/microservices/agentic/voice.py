from __future__ import annotations

from typing import Optional

from backend.schemas import TranscriptOut
from backend.src.repositories import TranscriptsRepository


class SpeechToTextClient:
    """Protocol-like base for STT clients."""

    def transcribe(self, audio_uri: str, language: Optional[str]) -> TranscriptOut:
        raise NotImplementedError


class WhisperClient(SpeechToTextClient):
    """Minimal Whisper client wrapper using a repository for state.

    This uses dummy behavior for now and does not call external APIs.
    """

    def __init__(self, transcripts_repo: TranscriptsRepository, api_key: str | None = None, model: str | None = None) -> None:
        self._repo = transcripts_repo
        self.api_key = api_key or "whisper-dummy"
        self.model = model or "whisper-1"

    def transcribe(self, audio_uri: str, language: Optional[str]) -> TranscriptOut:
        rec = self._repo.create_pending(user_id=None, audio_uri=audio_uri, language=language)  # type: ignore[arg-type]
        # Immediately mark done with dummy text
        return self._repo.mark_done(rec.id, text=f"Transcribed: {audio_uri}")


__all__ = ["SpeechToTextClient", "WhisperClient"]
