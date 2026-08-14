"""
RRVDXB Backend — app/ai/embeddings.py
Product embeddings for the AI recommender (Day 09).

TF-IDF over each product's name + description + category + brand, with cosine
similarity. Deliberately pure Python — no scikit-learn, no torch, no API call:
the catalogue is small, this runs in milliseconds at startup, and it keeps
requirements.txt light for the Render deploy on Day 10.

This is the cold-start path. A shopper with no order history still gets
content-similar products instead of a generic popularity list.

Owner: Ubaid Ullah Farooqui (UF)
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

# Words that carry no signal for product similarity.
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "of", "in", "on", "to",
    "your", "you", "this", "that", "it", "is", "are", "by", "from", "up",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def build_tfidf(documents: dict[int, str]) -> dict[int, dict[str, float]]:
    """documents: {product_id: text}. Returns L2-normalised tf-idf vectors."""
    if not documents:
        return {}

    tokenised = {pid: tokenize(text) for pid, text in documents.items()}

    doc_freq: Counter[str] = Counter()
    for tokens in tokenised.values():
        doc_freq.update(set(tokens))

    total_docs = len(tokenised)
    vectors: dict[int, dict[str, float]] = {}

    for pid, tokens in tokenised.items():
        if not tokens:
            vectors[pid] = {}
            continue
        counts = Counter(tokens)
        longest = max(counts.values())
        vector: dict[str, float] = {}
        for term, count in counts.items():
            tf = 0.5 + 0.5 * (count / longest)          # damped term frequency
            idf = math.log((total_docs + 1) / (doc_freq[term] + 1)) + 1.0
            vector[term] = tf * idf
        norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
        vectors[pid] = {term: value / norm for term, value in vector.items()}

    return vectors


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Both vectors are already L2-normalised, so this is a plain dot product."""
    if not a or not b:
        return 0.0
    if len(b) < len(a):
        a, b = b, a
    return sum(weight * b.get(term, 0.0) for term, weight in a.items())


def build_content_neighbours(
    documents: dict[int, str], top_k: int = 10, min_score: float = 0.05
) -> dict[int, list[tuple[int, float]]]:
    """
    Precompute the top-k content-similar products for every product.

    Inverted index first, so we only score pairs that share at least one term
    instead of every pair in the catalogue. Comfortable up to a few thousand
    products, which is well past what RRVDXB will hold during the sprint.
    """
    vectors = build_tfidf(documents)

    postings: dict[str, list[int]] = defaultdict(list)
    for pid, vector in vectors.items():
        for term in vector:
            postings[term].append(pid)

    neighbours: dict[int, list[tuple[int, float]]] = {}
    for pid, vector in vectors.items():
        candidates: set[int] = set()
        for term in vector:
            candidates.update(postings[term])
        candidates.discard(pid)

        scored = [
            (other, cosine(vector, vectors[other]))
            for other in candidates
        ]
        scored = [(o, s) for o, s in scored if s >= min_score]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        neighbours[pid] = scored[:top_k]

    return neighbours
