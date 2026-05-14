from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class NoteResult:
    title: str
    content_markdown: str
    kind: str  # one of NoteKind values
    summary_sentence: str = ""
    source_excerpt: str = ""
    why_it_matters: str = ""
    problem: str = ""
    core_insight: str = ""
    application: str = ""
    first_step: str = ""
    deeper_principle: str = ""
    context_tags: list[str] = field(default_factory=list)


class KnowledgeNoteProvider(Protocol):
    def generate(self, transcript_text: str, language_code: str = "") -> list[NoteResult]: ...


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]: ...


class SubstanceGateProvider(Protocol):
    def assess(self, text: str) -> int:
        """Return transformation potential score 0-10. >= threshold means proceed."""
        ...
