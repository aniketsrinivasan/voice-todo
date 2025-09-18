from __future__ import annotations

from backend.src.microservices.agentic.voice import WhisperClient
from backend.src.repositories import TranscriptsRepository


def main() -> None:
    repo = TranscriptsRepository()
    client = WhisperClient(transcripts_repo=repo, api_key="dummy", model="whisper-dummy")
    result = client.transcribe(audio_uri="supabase://bucket/path.wav", language="en")
    print("status:", result.status)
    print("text:", result.text)


if __name__ == "__main__":
    main()

