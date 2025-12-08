"""
AI4OHS-HYBRID public API kısayolları.

Bu dosya, çekirdek modüllerin inbound bağımlılığını sağlar ve dış kullanımlar için
ana fonksiyonları yeniden dışa aktarır.
"""

# Guarded inference (OHS uzmanı)
from agentic.guarded_inference import generate_guarded_response  # noqa: F401

# RAG/OCR yardımcıları
from genai.rag.document_loader import load_document  # noqa: F401
from genai.rag.ocr_ingest import ingest_image_to_chunks, ocr_image_to_text  # noqa: F401
from genai.rag.chunker import apply_rules as chunk_text  # noqa: F401

# Governance / uyum
from utils.compliance import (  # noqa: F401
    has_any_keyword,
    has_keywords,
    validate_ppe_requirements,
)

__all__ = [
    "generate_guarded_response",
    "load_document",
    "ingest_image_to_chunks",
    "ocr_image_to_text",
    "chunk_text",
    "has_any_keyword",
    "has_keywords",
    "validate_ppe_requirements",
]
