"""
OHS Sistem Prompt Oluşturucu
----------------------------

Amaç: Llama.cpp için iş güvenliği uzmanı rolünde, guardrail'li sistem prompt üretmek.
"""

from typing import List, Optional

from agentic.llama_learning_integration.llama_client import format_guarded_prompt
from governance.governance_policies import SAFETY_POLICIES, COMPLIANCE_POLICIES

DEFAULT_ROLE = (
    "Profesyonel iş sağlığı ve güvenliği uzmanısın. "
    "Türkçe yanıt ver; 6331, ISO 45001, OSHA ve IFC ESS'e göre en sıkı kuralı uygula. "
    "Önce elimine et / mühendislik / idari / KKD hiyerarşisiyle öneride bulun."
)


def _policy_lines(policies: List[dict]) -> List[str]:
    lines = []
    for p in policies:
        lines.append(f"- ({p['id']}) {p['description']}")
    return lines


def build_system_prompt(extra_instructions: Optional[str] = None) -> str:
    safety = "\n".join(_policy_lines(SAFETY_POLICIES))
    compliance = "\n".join(_policy_lines(COMPLIANCE_POLICIES))
    extras = extra_instructions.strip() if extra_instructions else ""

    blocks = [
        DEFAULT_ROLE,
        "Güvenlik politikaları:\n" + safety,
        "Mevzuat/uyum politikaları:\n" + compliance,
    ]
    if extras:
        blocks.append("Ek kurallar:\n" + extras)
    return "\n\n".join(blocks)


def build_guarded_completion_prompt(
    user_prompt: str,
    rag_context: str = "",
    compliance_mapping_hint: str = "",
    extra_instructions: Optional[str] = None,
) -> str:
    """
    Sistem + (isteğe bağlı) RAG context + kullanıcı prompt'unu tek metin halinde döndürür.
    """

    sys_prompt = build_system_prompt(extra_instructions)
    return format_guarded_prompt(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        context=rag_context,
        compliance_hint=compliance_mapping_hint,
    )
