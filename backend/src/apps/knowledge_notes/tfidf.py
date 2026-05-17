import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _term_frequency(tokens: list[str]) -> dict[str, float]:
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


def _inverse_document_frequency(tokenized_docs: list[list[str]]) -> dict[str, float]:
    doc_count = len(tokenized_docs)
    doc_frequency: Counter[str] = Counter()
    for tokens in tokenized_docs:
        doc_frequency.update(set(tokens))
    return {
        term: math.log((1 + doc_count) / (1 + frequency)) + 1.0
        for term, frequency in doc_frequency.items()
    }


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = _term_frequency(tokens)
    return {term: tf_value * idf.get(term, 0.0) for term, tf_value in tf.items()}


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    shared_terms = set(left) & set(right)
    numerator = sum(left[term] * right[term] for term in shared_terms)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def score_text_against_corpus(
    source_text: str,
    target_text: str,
    corpus_texts: list[str],
) -> float:
    tokenized_docs = [
        _tokenize(text)
        for text in [*corpus_texts, source_text, target_text]
        if text.strip()
    ]
    if len(tokenized_docs) < 2:
        return 0.0
    idf = _inverse_document_frequency(tokenized_docs)
    source_vector = _tfidf_vector(_tokenize(source_text), idf)
    target_vector = _tfidf_vector(_tokenize(target_text), idf)
    return _cosine_similarity(source_vector, target_vector)
