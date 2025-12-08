"""
AI4OHS-HYBRID
Self-Evaluation Driven Rewrite Flow

Amaç:
- SelfEvaluator skoruna göre cevap kalitesini kontrol etmek
- Belirli eşik altındaysa cevabı otomatik yeniden üretmek
- Llama.cpp cevap üretim fonksiyonunu dışarıdan enjekte edilebilir yapmak
"""

from typing import Any, Callable, Dict

from agentic.self_evaluator import SelfEvaluator
from governance.audit_logger import log_event


class RewriteFlow:
    def __init__(
        self,
        regenerate_fn: Callable[[str, Dict[str, Any]], str],
        threshold: float = 0.80,
        max_attempts: int = 2,
    ):
        """
        regenerate_fn: (prompt, metadata) -> new_answer_text
        threshold: self-eval overall_score için minimum eşik
        max_attempts: yeniden yazma denemesi sayısı
        """
        self.regenerate_fn = regenerate_fn
        self.threshold = threshold
        self.max_attempts = max_attempts
        self.evaluator = SelfEvaluator()

    def run(self, prompt: str, initial_answer: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dönen:
        {
          "answer": <final_answer>,
          "evaluation": {...},
          "attempts": n
        }
        """
        answer = initial_answer
        attempts = 1

        eval_result = self.evaluator.evaluate(answer, metadata)
        log_event("SELF_EVAL_INITIAL", "Initial evaluation", eval_result)

        while eval_result["overall_score"] < self.threshold and attempts <= self.max_attempts:
            feedback = (
                f"Previous answer overall_score={eval_result['overall_score']:.2f}. "
                f"Improve structure, compliance mapping and safety clarity."
            )

            metadata = dict(metadata or {})
            metadata["self_eval_feedback"] = feedback

            answer = self.regenerate_fn(prompt, metadata)
            attempts += 1
            eval_result = self.evaluator.evaluate(answer, metadata)
            log_event("SELF_EVAL_RETRY", "Retry evaluation", eval_result)

        return {"answer": answer, "evaluation": eval_result, "attempts": attempts}
