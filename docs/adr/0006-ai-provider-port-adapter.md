# ADR 0006: AI Provider Port/Adapter Pattern

## Status
Accepted

## Context
Transcription and summarization require external AI services (e.g., OpenAI Whisper) or local models.
Hardwiring a specific provider creates vendor lock-in and makes testing difficult.

## Decision
All AI integrations use a Port/Adapter pattern:
- `ports.py` defines Protocols (TranscriptionProvider, SummaryProvider)
- Concrete adapters live in `providers/` subdirectory
- Active provider is selected via `TRANSCRIPTION_PROVIDER` setting
- StubProvider is the default for local development and testing

## Consequences
- positive: provider can be swapped without changing business logic
- positive: tests can run without external API calls using StubProvider
- negative: slight indirection when adding new providers
