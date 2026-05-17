import json
import logging
import re

from openai import OpenAI

from ..ports import KnowledgeNoteProvider, NoteResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Du bist ein Transformations-Extraktions-Assistent. "
    "Du analysierst Transkripte und destillierst daraus persönliche Wachstums-Artefakte — "
    "keine Inhaltsangaben, sondern Erkenntnis-Kristalle die das Leben des Lesers "
    "konkret verändern können. "
    "Antworte NUR mit einem gültigen JSON-Array ohne Erklärungen oder Markdown."
)

_MAX_NOTE_WORDS = 80
_GENERIC_REFLECTION_PREFIXES = (
    "welche aussage aus dem inhalt",
    "welcher aussage aus dem inhalt",
    "was waere die wichtigste erkenntnis",
)
_GENERIC_ACTION_PHRASES = ("zum beispiel:",)
_MAX_SECTION_WORDS = 32
_MAX_SECTIONS = 6
_MAX_SENTENCES_PER_SECTION = 2
_ICH_FORM_PREFIXES = (
    "ich ",
    "mir ",
    "mich ",
    "mein ",
    "meine ",
    "meinem ",
    "meiner ",
    "i ",
    "my ",
    "me ",
    "i'",
)

_SUMMARIES_SECTION_TEMPLATE = (
    "KONTEXT — Zusammenfassungen (nur zur Themen-Orientierung, NICHT als Quelle zitieren):\n"
    "{summaries_block}\n\n"
)

_USER_PROMPT_TEMPLATE = (
    "{summaries_section}"
    "Analysiere das folgende Transkript. "
    "Nutze die Zusammenfassungen oben als Orientierung für wichtige Themen, "
    "wähle aber deine Ankerstellen und Zitate ausschließlich aus dem Transkript-Text unten.\n"
    "Identifiziere 3-6 Passagen mit echtem Transformations-Potenzial.\n\n"
    "WICHTIG: Überspringe flache, generische oder rein beschreibende Aussagen. "
    "Qualität vor Quantität.\n"
    "Wenn weniger als 3 hochwertige Erkenntnisse vorhanden sind, gib weniger zurück.\n\n"
    "Für jede Erkenntnis erzeuge ein JSON-Objekt mit exakt diesen Schlüsseln:\n\n"
    "- \"kind\": eines von \"insight\" | \"action\" | \"reflection\" | "
    "\"question\"\n"
    "- \"title\": Aktiver Titel in Ich-Form, max 10 Wörter "
    "(z.B. \"Ich erkenne, dass Konflikte Wachstum signalisieren\")\n"
    "- \"problem\": Was ist die Spannung, das Leid oder der unbefriedigte Zustand "
    "den dieser Inhalt adressiert? Max 2 Sätze.\n"
    "- \"core_insight\": Die Kern-Erkenntnis in Ich-Form — NICHT \"der Referent "
    "sagt X\" sondern \"Ich erkenne: X\". Max 2 Sätze.\n"
    "- \"application\": In welcher konkreten Lebenssituation wende ich das an? "
    "Woran merke ich sensorisch dass es wirkt? Max 2 Sätze.\n"
    "- \"first_step\": Der kleinste mögliche erste Schritt — konkret, heute noch "
    "umsetzbar, MUSS mit einem Verb beginnen. 1 Satz.\n"
    "- \"deeper_principle\": Das übergeordnete Prinzip dahinter — auf welche "
    "anderen Lebensbereiche anwendbar? 1 Satz.\n"
    "- \"context_tags\": Array von passenden Tags aus dieser Liste (wähle 1-3): "
    "[\"kontext:Entscheidung\", \"kontext:Konflikt\", "
    "\"kontext:Antriebslosigkeit\", \"kontext:Beziehung\", "
    "\"kontext:Arbeit\", \"kontext:Selbstbild\", "
    "\"kontext:Kommunikation\", \"kontext:Gewohnheit\", "
    "\"kontext:Führung\", \"kontext:Kreativität\", \"kontext:Verlust\", "
    "\"kontext:Unsicherheit\"]\n"
    "- \"summary_sentence\": Eine kurze Zusammenfassung der Kernaussage "
    "(1 Satz, für Rückwärtskompatibilität)\n"
    "- \"source_excerpt\": Kurzes Zitat oder paraphrasierter Anker aus dem "
    "Transkript (max 20 Wörter)\n"
    "- \"why_it_matters\": Ein Satz warum diese Erkenntnis erhaltenswert ist\n"
    "- \"content_markdown\": Vertiefende Ausführung in Markdown "
    "(max 3 Bullets oder 2 kurze Absätze)\n\n"
    "Regeln:\n"
    "- title MUSS in Ich-Form beginnen (\"Ich erkenne\", \"Ich verstehe\", "
    "\"Mir wird klar\", etc.)\n"
    "- first_step MUSS mit einem Verb im Imperativ beginnen "
    "(z.B. \"Schreibe...\", \"Frage...\", \"Beobachte...\")\n"
    "- problem MUSS ausgefüllt sein — keine Erkenntnis ohne Spannung\n"
    "- source_excerpt MUSS aus dem Transkript-Text unten stammen, NICHT aus den Zusammenfassungen\n"
    "- Schreibe in der Sprache des Transkripts\n"
    "- Gib NUR das JSON-Array zurück, keine Erklärungen, kein Markdown-Wrapper\n\n"
    "Transkript (Primärquelle für Ankerstellen und Zitate):\n"
    "{transcript}\n"
)


def _word_count(text: str) -> int:
    return len(text.split())


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()


def _looks_like_generic_reflection(text: str) -> bool:
    normalized = _normalize_whitespace(text).lower()
    return normalized.startswith(_GENERIC_REFLECTION_PREFIXES)


def _looks_like_generic_action(text: str) -> bool:
    normalized = _normalize_whitespace(text).lower()
    return any(phrase in normalized for phrase in _GENERIC_ACTION_PHRASES)


def _filter_note_results(results: list[NoteResult]) -> list[NoteResult]:
    filtered: list[NoteResult] = []
    seen_signatures: set[tuple[str, str, str]] = set()
    for result in results:
        content = _normalize_whitespace(result.content_markdown)
        summary_sentence = _normalize_whitespace(result.summary_sentence)
        source_excerpt = _normalize_whitespace(result.source_excerpt)
        why_it_matters = _normalize_whitespace(result.why_it_matters)
        problem = _normalize_whitespace(result.problem)
        core_insight = _normalize_whitespace(result.core_insight)
        application = _normalize_whitespace(result.application)
        first_step = _normalize_whitespace(result.first_step)
        deeper_principle = _normalize_whitespace(result.deeper_principle)
        context_tags = result.context_tags if isinstance(result.context_tags, list) else []
        if not content:
            continue
        if _word_count(content) > _MAX_NOTE_WORDS:
            continue
        if not summary_sentence or not source_excerpt or not why_it_matters:
            continue
        title = result.title.strip()[:255]
        title_lower = title.lower()
        if not any(title_lower.startswith(prefix) for prefix in _ICH_FORM_PREFIXES):
            continue
        if not problem:
            continue
        if not first_step or len(first_step.split()) < 4:
            continue
        if result.kind == "reflection" and _looks_like_generic_reflection(content):
            continue
        if result.kind == "action" and _looks_like_generic_action(content):
            continue
        signature = (result.kind, title_lower, content.lower())
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        filtered.append(
            NoteResult(
                title=title,
                content_markdown=content,
                kind=result.kind,
                summary_sentence=summary_sentence,
                source_excerpt=source_excerpt,
                why_it_matters=why_it_matters,
                problem=problem,
                core_insight=core_insight,
                application=application,
                first_step=first_step,
                deeper_principle=deeper_principle,
                context_tags=context_tags,
            )
        )
    return filtered


def _extract_sentences(transcript_text: str) -> list[str]:
    condensed_text = _normalize_whitespace(transcript_text)
    parts = re.split(r"(?<=[.!?])\s+", condensed_text)
    return [part.strip(" .") for part in parts if part.strip()]


def _chunk_sentences(
    sentences: list[str],
    max_section_words: int = _MAX_SECTION_WORDS,
    max_sentences_per_section: int = _MAX_SENTENCES_PER_SECTION,
) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        sentence_words = _word_count(sentence)
        if current and (
            current_words + sentence_words > max_section_words
            or len(current) >= max_sentences_per_section
        ):
            chunks.append(current)
            current = [sentence]
            current_words = sentence_words
            continue
        current.append(sentence)
        current_words += sentence_words

    if current:
        chunks.append(current)
    return chunks


def _pick_focus_sentence(chunk: list[str]) -> str:
    return max(chunk, key=lambda sentence: (_word_count(sentence), -chunk.index(sentence)))


def _build_transcript_sections(
    transcript_text: str,
    max_section_words: int = _MAX_SECTION_WORDS,
    max_sections: int = _MAX_SECTIONS,
) -> list[dict[str, str]]:
    sentences = _extract_sentences(transcript_text)
    chunks = _chunk_sentences(sentences, max_section_words=max_section_words)
    if len(chunks) <= max_sections:
        selected_chunks = chunks
    else:
        selected_chunks = []
        last_index = len(chunks) - 1
        for index in range(max_sections):
            raw_position = round(index * last_index / (max_sections - 1))
            chunk = chunks[raw_position]
            if selected_chunks and chunk == selected_chunks[-1]:
                continue
            selected_chunks.append(chunk)

    return [
        {
            "focus_sentence": _pick_focus_sentence(chunk),
            "excerpt": " ".join(chunk),
        }
        for chunk in selected_chunks
    ]


_SUMMARY_KIND_LABELS: dict[str, str] = {
    "short": "Kurzzusammenfassung",
    "detailed": "Detailzusammenfassung",
    "bullet": "Bullet-Zusammenfassung",
}


def _build_summaries_section(summaries: dict[str, str]) -> str:
    if not summaries:
        return ""
    lines: list[str] = []
    for kind in ("short", "detailed", "bullet"):
        if kind in summaries:
            label = _SUMMARY_KIND_LABELS.get(kind, kind)
            lines.append(f"[{label}]\n{summaries[kind][:1500]}")
    for kind, body in summaries.items():
        if kind not in ("short", "detailed", "bullet"):
            lines.append(f"[{kind}]\n{body[:1500]}")
    if not lines:
        return ""
    block = "\n\n".join(lines)
    return _SUMMARIES_SECTION_TEMPLATE.format(summaries_block=block)


def _build_prompt_context(transcript_text: str) -> str:
    sections = _build_transcript_sections(transcript_text)
    if not sections:
        return transcript_text[:12000]

    section_lines = [
        f"{index}. Focus: {section['focus_sentence']}\nExcerpt: {section['excerpt']}"
        for index, section in enumerate(sections, start=1)
    ]
    return "\n\n".join(section_lines)[:12000]


def _extract_json_array(raw_content: str) -> list[object]:
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        pass
    else:
        return parsed if isinstance(parsed, list) else []

    start = raw_content.find("[")
    end = raw_content.rfind("]") + 1
    if start == -1 or end == 0:
        raise json.JSONDecodeError("No JSON array found", raw_content, 0)

    candidate = raw_content[start:end]
    parsed = json.loads(candidate)
    return parsed if isinstance(parsed, list) else []


class OpenAICompatibleNoteProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self.model = model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    def generate(
        self,
        transcript_text: str,
        language_code: str = "",
        summaries: dict[str, str] | None = None,
    ) -> list[NoteResult]:
        summaries_section = _build_summaries_section(summaries) if summaries else ""
        prompt = _USER_PROMPT_TEMPLATE.format(
            summaries_section=summaries_section,
            transcript=_build_prompt_context(transcript_text),
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            max_tokens=2048,
            temperature=0.4,
        )
        raw_content = (response.choices[0].message.content or "").strip()

        try:
            items = _extract_json_array(raw_content)
        except json.JSONDecodeError:
            logger.warning("Note provider returned non-JSON response; attempting extraction")
            logger.error("Could not extract JSON array from note provider response")
            return []

        results = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            kind = raw.get("kind", "general")
            title = str(raw.get("title", "Untitled"))[:255]
            content = str(raw.get("content_markdown", ""))
            results.append(
                NoteResult(
                    title=title,
                    content_markdown=content,
                    kind=kind,
                    summary_sentence=str(raw.get("summary_sentence", "")),
                    source_excerpt=str(raw.get("source_excerpt", "")),
                    why_it_matters=str(raw.get("why_it_matters", "")),
                    problem=str(raw.get("problem", "")),
                    core_insight=str(raw.get("core_insight", "")),
                    application=str(raw.get("application", "")),
                    first_step=str(raw.get("first_step", "")),
                    deeper_principle=str(raw.get("deeper_principle", "")),
                    context_tags=raw.get("context_tags", [])
                    if isinstance(raw.get("context_tags"), list)
                    else [],
                )
            )

        return _filter_note_results(results)


def get_note_provider() -> KnowledgeNoteProvider:
    from django.conf import settings

    return OpenAICompatibleNoteProvider(
        base_url=settings.AI_HUB_BASE_URL,
        api_key=settings.AI_HUB_API_KEY,
        model=settings.AI_HUB_MODEL,
    )
