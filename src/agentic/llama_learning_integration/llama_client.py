import json
import os
import time
from typing import Any, Dict, Optional

import requests

LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080/completion")
LLAMA_REQUEST_TIMEOUT = float(os.getenv("LLAMA_REQUEST_TIMEOUT", "120"))
LLAMA_CTX_LIMIT = int(os.getenv("LLAMA_CTX_LIMIT", "4096"))
LLAMA_MAX_RETRIES = int(os.getenv("LLAMA_MAX_RETRIES", "2"))
DEFAULT_STOP = ["<|eot_id|>", "<|end_of_text|>"]


class LlamaCPPError(RuntimeError):
    """Llama.cpp erişim ve format hataları."""


def _approx_tokens(text: str) -> int:
    """Basit ~4 karakter = 1 token yaklaşımı."""

    return max(1, len(text) // 4)


def _post_with_retry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """HTTP POST + basit retry; hata metnini korur."""

    last_error: Optional[Exception] = None

    for attempt in range(LLAMA_MAX_RETRIES + 1):
        try:
            resp = requests.post(LLAMA_SERVER_URL, json=payload, timeout=LLAMA_REQUEST_TIMEOUT)
            if resp.status_code != 200:
                short_text = resp.text[:2000]
                raise LlamaCPPError(
                    f"Llama.cpp HTTP {resp.status_code}. Body (truncated): {short_text}"
                )
            return resp.json()
        except (requests.RequestException, ValueError, LlamaCPPError) as exc:
            last_error = exc
            if attempt < LLAMA_MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise LlamaCPPError(f"Llama.cpp request failed: {exc}") from exc

    raise LlamaCPPError(f"Llama.cpp request failed: {last_error}")


def _validate_ctx(prompt: str, n_predict: int) -> None:
    """Ctx sınırına göre kaba kontrol yapar; aşımda erken hata verir."""

    approx = _approx_tokens(prompt) + max(1, n_predict)
    if approx > LLAMA_CTX_LIMIT:
        raise LlamaCPPError(
            f"Prompt + completion tahmini (~{approx} token) LLAMA_CTX_LIMIT "
            f"{LLAMA_CTX_LIMIT}'i aşıyor. Promptu kısaltın veya n_predict düşürün."
        )


def llama_cpp(
    prompt: str,
    n_predict: int = 512,
    *,
    temperature: float = 0.2,
    top_p: float = 0.9,
    stop: Optional[list[str]] = None,
    stream: bool = False,
) -> str:
    """
    Llama.cpp /completion çağrısı (deterministik ayarlarla).

    - ctx sınırı için kaba kontrol
    - timeout + retry
    - content/completion alanı dönüş
    """

    _validate_ctx(prompt, n_predict)

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": temperature,
        "top_p": top_p,
        "stop": stop or DEFAULT_STOP,
        "stream": stream,
    }

    data = _post_with_retry(payload)

    if isinstance(data, dict):
        if isinstance(data.get("content"), str):
            return data["content"]
        if isinstance(data.get("completion"), str):
            return data["completion"]

    # Beklenmeyen formatta ise ham JSON stringle döndür
    return json.dumps(data, ensure_ascii=False)


def format_guarded_prompt(
    system_prompt: str,
    user_prompt: str,
    *,
    context: str = "",
    compliance_hint: str = "",
) -> str:
    """
    Basit “chat” stili şablon: sistem + (opsiyonel) context + kullanıcı.
    Llama.cpp text completion için tek string döner.
    """

    parts = [
        f"### System:\n{system_prompt.strip()}",
    ]
    if context.strip():
        parts.append(f"### Context:\n{context.strip()}")
    if compliance_hint.strip():
        parts.append(f"### Compliance:\n{compliance_hint.strip()}")
    parts.append(f"### User:\n{user_prompt.strip()}\n### Assistant:")
    return "\n\n".join(parts)


def _parse_json_loose(text: str) -> Dict[str, Any]:
    """JSON parse; başarısızsa gövde içindeki ilk {...} bloğunu dener."""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:  # pragma: no cover - sadece hata yolu
            raise LlamaCPPError(f"Llama.cpp JSON parse hatası: {exc}") from exc

    raise LlamaCPPError("Llama.cpp JSON bekleniyordu ancak parse edilemedi.")


def llama_cpp_json(prompt: str, n_predict: int = 512, **kwargs: Any) -> Dict[str, Any]:
    """
    JSON beklenen yanıtlar için yardımcı.
    Yanıtı parse eder, başarısız olursa LlamaCPPError fırlatır.
    """

    text = llama_cpp(prompt, n_predict=n_predict, **kwargs)
    return _parse_json_loose(text)
