"""
AI4OHS-HYBRID - Unified Pipeline Runner (Optimized)
Amaç: ingestion → staging → processed → embeddings → FAISS pipeline’larını
sadece değişiklik olduğunda çalıştırmak (delta-based execution).
"""

import os

from genai.rag.chunkers import chunk_documents
from genai.rag.loaders import load_and_convert
from genai.rag.pipelines import rebuild_index_if_needed
from genai.rag.retrievers import build_embeddings
from governance.audit_logger import log_event

from zeus_layer.file_sanitizer import sanitize_directory


def run_all():
    log_event("PIPELINE_START", "Pipeline execution triggered manually.")

    sanitize_directory("data/raw")
    load_and_convert("data/raw", "data/staging")
    chunk_documents("data/staging", "data/processed")
    build_embeddings("data/processed", "data/embeddings")
    rebuild_index_if_needed()

    log_event("PIPELINE_COMPLETE", "All pipelines completed successfully.")

    log_event("PIPELINE_COMPLETE", "All pipelines completed successfully.")
