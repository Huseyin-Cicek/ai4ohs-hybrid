from .chunking_rules import CHUNK_RULES

"""
Chunker v2.0 – HSSE Mevzuat + ESS Doküman Optimizasyonu
"""



def apply_rules(text: str, doc_type: str):
    rules = CHUNK_RULES.get(doc_type, CHUNK_RULES["general"])
    chunks, current = [], ""

    for line in text.split("\n"):
        if any(marker in line for marker in rules["split_on"]):
            if len(current) > rules["min"]:
                chunks.append(current.strip())
                current = ""
        current += line + "\n"

        if len(current) > rules["max"]:
            chunks.append(current.strip())
            current = ""

    if len(current.strip()) > 0:
        chunks.append(current.strip())

    merged = []
    buffer = ""
    for c in chunks:
        if len(c) < rules["merge_threshold"]:
            buffer += c + "\n"
        else:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(c.strip())

    if buffer:
        merged.append(buffer.strip())

    return merged
    return merged
