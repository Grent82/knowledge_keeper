from dataclasses import dataclass
from typing import Protocol


@dataclass
class NoteResult:
    title: str
    content_markdown: str
    kind: str  # one of NoteKind values
    summary_sentence: str = ""
    source_excerpt: str = ""
    why_it_matters: str = ""


class KnowledgeNoteProvider(Protocol):
    def generate(self, transcript_text: str, language_code: str = "") -> list[NoteResult]: ...
