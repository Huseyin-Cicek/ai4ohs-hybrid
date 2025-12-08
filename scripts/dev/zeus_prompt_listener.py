"""
Zeus Prompt Listener
--------------------
- Wake word ve sesli komut yok.
- CLI üzerinden ">> " prompt'u ile komut alır.
- Başlangıçta "merhaba üstad" yazar, "çık" / "exit" ile kapanır.
- Tanınan komut yoksa metni llama.cpp'ye gönderir, cevabı yazdırır.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.dev.zeus_listener import ZeusVoiceListener  # komut haritası için
from src.agentic.llama_learning_integration.llama_client import LlamaCPPError, llama_cpp
from src.utils.regulations_lookup import find_articles


def main():
    listener = ZeusVoiceListener()
    print("merhaba üstad")
    print("Komutlar: " + ", ".join(listener.commands.keys()))
    print("Komut bulunamazsa soru/istek llama.cpp'ye gönderilir.")
    print("Çıkmak için: exit / çık")

    while True:
        try:
            cmd = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in {"exit", "çık", "quit"}:
            break

        matched = None
        for key in listener.commands:
            if key in cmd:
                matched = key
                break

        if matched:
            try:
                listener.commands[matched]()
            except Exception as exc:  # noqa: BLE001
                print(f"Komut hata verdi: {exc}")
        else:
            # Önce mevzuat araması yap
            articles = find_articles(cmd)
            # Eğer yüksek öncelikli (99 puanlı) mevzuat linki varsa direkt yaz ve devam et
            if articles:
                top_link = next((a for a in articles if a.get("score", 0) >= 90), None)
                if top_link and top_link.get("text", "").startswith("http"):
                    print(f"{top_link.get('ref')}: {top_link.get('text')}")
                    continue

            context = ""
            if articles:
                ctx_lines = []
                for a in articles:
                    ctx_lines.append(f"{a['ref']}: {a['text']}")
                context = "\n".join(ctx_lines)

            # Serbest metni llama.cpp'ye ilet (kısa, tekrarsız Türkçe yanıt)
            prompt = (
                "You are the AI4OHS-HYBRID assistant.\n"
                "Answer in Turkish, concise (en fazla 3 cümle), net ve tekrarsız.\n"
                "Bilgi yoksa 'bilmiyorum' de. Liste gerekiyorsa 5 maddeden fazla verme.\n"
                "Yasal madde istenirse sadece özeti ve madde numarasını ver.\n"
                f"Kontekst:\n{context}\n"
                f"Kullanıcı: {cmd}\nCevap:"
            )
            try:
                resp = llama_cpp(prompt, n_predict=128)
                print(resp)
            except LlamaCPPError as exc:
                if "connection error" in str(exc).lower():
                    print(
                        "llama.cpp sunucusuna bağlanılamadı. "
                        "LLAMA_SERVER_URL ortam değişkeniyle URL/port ayarlayabilir "
                        "veya sunucuyu başlatabilirsiniz (varsayılan: http://127.0.0.1:8080/completion)."
                    )
                else:
                    print(f"llama.cpp hatası: {exc}")


if __name__ == "__main__":
    main()
