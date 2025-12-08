"""
AI4OHS-HYBRID — Zeus Startup Tasks v4.0
---------------------------------------

Bu modül sistem açılır açılmaz aşağıdaki işlemleri yapar:

1) File sanitization (zararlı karakter/bozuk dosya temizliği)
2) ETL normalization (raw → staging → processed)
3) Embedding generation + FAISS index kontrolü
4) Learning Engine cycle (code + knowledge learning)
5) Auto-Optimizer (kod örüntüsü analiz + refactor önerisi)
6) Predictive Optimization Engine pre-warm
7) Autonomous Developer Mode safety-check
8) Startup audit logging

Tüm görevler offline ve güvenlik filtresi altındadır.
"""

import os

from agents.autonomous_developer_mode import AutonomousDeveloperMode
from ai_ml.predictive.predictive_optimization_engine import PredictiveOptimizationEngine

from agentic.memory.code_learning_engine import CodeLearningEngine
from genai.rag.pipelines import rebuild_index_if_needed
from governance.audit_logger import log_event
from zeus_layer.auto_ml_worker import run_etl_pipelines
from zeus_layer.auto_optimizer import run_auto_optimizer
from zeus_layer.file_sanitizer import sanitize_directory

RAW_DIR = "data/raw"
STAGING_DIR = "data/staging"
PROCESSED_DIR = "data/processed"


def boot_sequence():
    log_event("ZEUS_STARTUP", "System boot sequence started")

    # 1) Raw data sanitization
    sanitize_directory(RAW_DIR)
    log_event("SANITIZE", f"Sanitization completed for {RAW_DIR}")

    # 2) ETL: raw → staging → processed
    run_etl_pipelines()
    log_event("ETL", "Normalization and markdown conversion pipeline executed")

    # 3) Rebuild FAISS index if needed
    rebuild_index_if_needed()
    log_event("FAISS", "Vector index verified")

    # 4) Learning engine: code + knowledge pattern learning
    cle = CodeLearningEngine()
    patterns = cle.run_learning_cycle()
    log_event("LEARNING", "Code learning cycle completed", {"patterns": patterns})

    # 5) Auto Optimization Plan (non-destructive)
    auto_opt_plan = run_auto_optimizer()
    log_event("AUTO_OPT_PLAN", "Code optimization plan generated", auto_opt_plan)

    # 6) Predictive Optimization Engine warm-up
    poe = PredictiveOptimizationEngine()
    poe.initialize_models()
    log_event("POE_INIT", "Predictive Optimization Engine initialized")

    # 7) Autonomous Developer Mode — restricted & safe
    adm = AutonomousDeveloperMode()
    adm.safety_check()
    log_event("ADM_CHECK", "Autonomous Developer Mode safety check completed")

    # 8) Final system ready
    log_event("ZEUS_READY", "AI4OHS-HYBRID system ready")
    log_event("ZEUS_READY", "AI4OHS-HYBRID system ready")
