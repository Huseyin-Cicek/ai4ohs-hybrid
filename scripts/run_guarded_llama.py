"""
Guarded Llama.cpp Çalıştırıcısı
-------------------------------

Kullanım:
  python scripts/run_guarded_llama.py "Saha kazısı için güvenli çalışma adımlarını yaz."

Çıktı: Sistem prompt + guardrails + (opsiyonel) context ile Llama.cpp yanıtı.
"""

import argparse
import json

from agentic.guarded_inference import generate_guarded_response
from agentic.llama_learning_integration.llama_client import llama_cpp
from genai.prompting.ohs_prompt_builder import build_guarded_completion_prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Kullanıcı promptu")
    parser.add_argument("--context", help="RAG context", default="")
    parser.add_argument("--hint", help="Uyum ipucu / madde referansları", default="")
    parser.add_argument("--extra", help="Ek kurallar", default="")
    parser.add_argument(
        "--self-eval",
        action="store_true",
        help="SelfEvaluator + RewriteFlow ile threshold altı yanıtları otomatik yeniden yaz",
    )
    parser.add_argument("--threshold", type=float, default=0.80, help="Self-eval eşik")
    parser.add_argument("--max-attempts", type=int, default=2, help="Yeniden yazma denemesi")
    args = parser.parse_args()

    if args.self_eval:
        result = generate_guarded_response(
            user_prompt=args.prompt,
            rag_context=args.context,
            compliance_hint=args.hint,
            extra_instructions=args.extra,
            threshold=args.threshold,
            max_attempts=args.max_attempts,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        full_prompt = build_guarded_completion_prompt(
            user_prompt=args.prompt,
            rag_context=args.context,
            compliance_mapping_hint=args.hint,
            extra_instructions=args.extra,
        )
        result = llama_cpp(full_prompt, n_predict=512)
        print(result)


if __name__ == "__main__":
    main()
