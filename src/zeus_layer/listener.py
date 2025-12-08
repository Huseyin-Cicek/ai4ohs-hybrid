"""
Zeus Voice Listener – Offline Llama Command Routing v3.0
Yeni: "Generate KPI dashboard for last quarter" entegrasyonu
"""

from subprocess import call

import speech_recognition as sr

from governance.audit_logger import log_event

WAKE = "hey zeus"


def interpret_command(text: str):
    text = text.lower()

    # Ingestion
    if "ingestion" in text or "pipeline" in text:
        log_event("VOICE_CMD", "User triggered ingestion pipeline.")
        call(["python", "scripts/run_all_pipelines.py"])
        return "Ingestion pipeline executed."

    # Incident summary
    if "incident" in text and "summary" in text:
        log_event("VOICE_CMD", "Incident summary requested.")
        # Burada ilgili agent tetiklenebilir
        return "Triggering incident analyzer..."

    # Rebuild index
    if "rebuild index" in text or "rebuild vector" in text:
        log_event("VOICE_CMD", "Vector index rebuild requested.")
        call(["python", "scripts/rebuild_indexes.py"])
        return "FAISS index rebuild executed."

    # KPI dashboard for last quarter
    if "kpi" in text and "dashboard" in text and "quarter" in text:
        log_event("VOICE_CMD", "Quarterly KPI dashboard requested.")
        call(["python", "scripts/generate_quarter_dashboard.py"])
        return "Quarterly KPI dashboard generated."

    return "Command recognized but no matching action."


def listen_loop():
    r = sr.Recognizer()
    mic = sr.Microphone()

    while True:
        with mic as source:
            audio = r.listen(source)

        try:
            text = r.recognize_sphinx(audio).lower()
        except:
            continue

        if WAKE in text:
            cmd = text.replace(WAKE, "").strip()
            response = interpret_command(cmd)
            print(response)
            log_event("VOICE_RESPONSE", response)
            print(response)
            log_event("VOICE_RESPONSE", response)
