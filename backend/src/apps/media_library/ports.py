from typing import Protocol


class TaggingProvider(Protocol):
    def suggest_tags(self, source_text: str) -> list[str]:
        """Return a list of 3-5 lowercase German tag names derived from source_text."""
        ...
