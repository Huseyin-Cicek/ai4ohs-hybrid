"""
RAG Chunking Rules v2.0 for AI4OHS-HYBRID
6331, ESS, ISO, PTW ve OHS raporları için optimize edilmiş chunklama.
"""

CHUNK_RULES = {
    "regulation": {
        "min": 250,
        "max": 900,
        "split_on": ["MADDE ", "Madde ", "Clause ", "Article "],
        "merge_threshold": 200,
    },
    "ess": {
        "min": 250,
        "max": 1000,
        "split_on": ["ESS", "Guidance Note", "GN"],
        "merge_threshold": 200,
    },
    "iso": {
        "min": 200,
        "max": 700,
        "split_on": ["4.", "5.", "6.", "7.", "8.", "9.", "10."],
        "merge_threshold": 150,
    },
    "incident_report": {
        "min": 300,
        "max": 1200,
        "split_on": ["Incident", "Root Cause", "Corrective", "Preventive"],
        "merge_threshold": 300,
    },
    "general": {"min": 300, "max": 1000, "split_on": ["\n\n", ".", ";"], "merge_threshold": 180},
}
