"""
AI4OHS-HYBRID
Llama.cpp Memory Compression (Context Optimizer)

Amaç:
- Konuşma geçmişini, Llama.cpp'nin context sınırı içinde kalacak şekilde sıkıştırmak
- System prompt, kritik kararlar, mevzuat atıfları korunur
- Detay cümleler özetlenerek context'e geri yazılır
"""

from typing import Dict, List

PRIORITY_ROLES = ["system", "developer"]
MAX_TOKENS = 7500  # ctx ~8192 için güvenli sınır
HARD_KEEP_LAST = 8  # En son n mesajı tam koru


def rough_token_count(text: str) -> int:
    # Basit approx: 1 token ~ 4 karakter
    return max(1, len(text) // 4)


def summarize_messages(messages: List[Dict]) -> str:
    """
    Llama.cpp'ye gönderilmeden önce basit bir özet üretmek için kullanılabilir.
    Burada lightweight, rule-based bir summarizer var;
    istenirse LLM tabanlı summarizer ile de değiştirilebilir.
    """
    bullets = []
    for m in messages:
        content = m.get("content", "")
        if not content:
            continue
        line = content.split("\n")[0]
        if len(line) > 200:
            line = line[:197] + "..."
        bullets.append(f"- {m['role']}: {line}")
    return "\n".join(bullets)


def compress_for_llama(messages: List[Dict]) -> List[Dict]:
    """
    messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
    Dönen: context sınırına uyan optimize edilmiş mesaj listesi.
    """
    # 1) System / developer mesajlarını aynen koru
    system_msgs = [m for m in messages if m["role"] in PRIORITY_ROLES]

    other = [m for m in messages if m["role"] not in PRIORITY_ROLES]
    if len(other) <= HARD_KEEP_LAST:
        return system_msgs + other

    # 2) Son HARD_KEEP_LAST mesajı tam koru
    keep_tail = other[-HARD_KEEP_LAST:]
    compress_zone = other[:-HARD_KEEP_LAST]

    # 3) Compress_zone için özet oluştur
    summary_content = summarize_messages(compress_zone)
    summary_msg = {
        "role": "system",
        "content": "Previous conversation compressed summary:\n" + summary_content,
    }

    combined = system_msgs + [summary_msg] + keep_tail

    # 4) Token sınırını kaba olarak kontrol et
    total_tokens = sum(rough_token_count(m["content"]) for m in combined)

    # Eğer hala çok uzun ise (çok ekstrem durum), tail'i kısalt
    while total_tokens > MAX_TOKENS and len(keep_tail) > 3:
        keep_tail = keep_tail[1:]  # en eski tail mesajını at
        combined = system_msgs + [summary_msg] + keep_tail
        total_tokens = sum(rough_token_count(m["content"]) for m in combined)

    return combined
