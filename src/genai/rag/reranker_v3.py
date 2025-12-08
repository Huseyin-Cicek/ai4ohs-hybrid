"""
RAG Re-Ranker v3.0 — AI4OHS-HYBRID
Hybrid scoring: semantic similarity + safety domain weighting.
Fully offline; llama.cpp-assisted scoring optional.
"""

import numpy as np
from sentence_transformers import CrossEncoder

# Stage 1: fast semantic scoring
SEM_MODEL = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

SAFETY_KEYWORDS = [
    "6331",
    "MADDE",
    "Madde",
    "ESS",
    "community safety",
    "ISO 45001",
    "risk",
    "hazard",
    "PPE",
    "engineering controls",
    "permit",
    "PTW",
    "corrective",
    "preventive",
]


def safety_weight(chunk_text: str) -> float:
    score = 1.0
    for kw in SAFETY_KEYWORDS:
        if kw.lower() in chunk_text.lower():
            score += 0.25
    return score


# Stage 2: optional llama.cpp micro-score
def llama_micro_score(prompt, model_fn=None):
    """
    model_fn: callable(text) → float
    You can bind llama.cpp scoring here.
    """
    if model_fn:
        return model_fn(prompt)
    return 1.0


def rerank_v3(query: str, candidates: list, llama_scorer=None, top_k=6):
    """
    candidates = [{"text": "...", "meta": {...}}, ...]
    Returns best-scored chunks.
    """
    texts = [c["text"] for c in candidates]
    sem_scores = SEM_MODEL.predict([(query, t) for t in texts])

    final_scores = []
    for i, c in enumerate(candidates):
        sw = safety_weight(c["text"])
        lm = llama_micro_score(c["text"], llama_scorer)
        score = sem_scores[i] * sw * lm
        final_scores.append((score, c))

    final_scores.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in final_scores[:top_k]]
