"""
Guarded inference helper:
- Sistem prompt + RAG context + uyum ipucu ile Llama.cpp çağrısı
- SelfEvaluator + RewriteFlow ile otomatik yeniden yazım (threshold altıysa)
"""

from typing import Any, Dict, Optional

from agentic.llama_learning_integration.llama_client import llama_cpp
from agentic.self_eval_rewrite_flow import RewriteFlow
from agentic.self_evaluator import SelfEvaluator
from genai.prompting.ohs_prompt_builder import build_guarded_completion_prompt
from governance.cag_rules_engine import CAGRulesEngine
from governance.ess_compliance_scorer import ess_score_from_items
from utils.compliance import validate_document


def _regen_fn(prompt: str, metadata: Dict[str, Any]) -> str:
    """RewriteFlow için yeniden üretici."""

    return llama_cpp(prompt, n_predict=512)


def generate_guarded_response(
    user_prompt: str,
    *,
    rag_context: str = "",
    compliance_hint: str = "",
    extra_instructions: str = "",
    threshold: float = 0.80,
    max_attempts: int = 2,
    run_cag: bool = True,
    ess_items: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Tek noktadan güvenli yanıt üretir.

    Dönüş:
      {
        "answer": <metin>,
        "evaluation": {...},
        "attempts": n,
        "prompt": <kullanılan birleşik prompt>,
        "compliance": {...} (isteğe bağlı CAG/ESS özeti)
      }
    """

    full_prompt = build_guarded_completion_prompt(
        user_prompt=user_prompt,
        rag_context=rag_context,
        compliance_mapping_hint=compliance_hint,
        extra_instructions=extra_instructions,
    )

    evaluator = SelfEvaluator()
    flow = RewriteFlow(regenerate_fn=lambda p, m: _regen_fn(p, m), threshold=threshold, max_attempts=max_attempts)

    # İlk yanıt
    initial_answer = llama_cpp(full_prompt, n_predict=512)

    metadata: Dict[str, Any] = {
        "compliance_mapping": [],  # mevcut mapping bilinmiyor; CAG sonrası doldurulabilir
        "user_prompt": user_prompt,
    }

    result = flow.run(full_prompt, initial_answer, metadata)
    result["prompt"] = full_prompt

    # CAG/ESS doğrulama (hafif, hata yutulur)
    if run_cag:
        compliance_summary: Dict[str, Any] = {}
        try:
            comp = validate_document(
                text=user_prompt + "\n" + rag_context,
                standards=["ISO45001", "OSHA", "LAW6331", "WB_ESS"],
                context={},
                categories=None,
            )
            compliance_summary["ok"] = comp.ok
            compliance_summary["violations"] = comp.violations
            compliance_summary["warnings"] = comp.warnings
            compliance_summary["stats"] = comp.stats
        except Exception as exc:
            compliance_summary["error"] = f"CAG validation failed: {exc}"

        try:
            if ess_items:
                ess_summary = ess_score_from_items(ess_items)
                compliance_summary["ess_score"] = ess_summary
        except Exception as exc:
            compliance_summary["ess_error"] = str(exc)

        try:
            # Rulepack meta (yükleme testi)
            rules_count = len(CAGRulesEngine().list_rules())
            compliance_summary["rule_count"] = rules_count
        except Exception:
            pass

        result["compliance"] = compliance_summary

    return result
