import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

REG_PATH = Path(__file__).resolve().parents[2] / "docs" / "compliance" / "turkish_regulations.json"
REGISTRY_MD = Path(__file__).resolve().parents[2] / "docs" / "compliance" / "check_turkish_law_registry.md"


@lru_cache(maxsize=1)
def _load_regulations() -> Dict:
    if not REG_PATH.exists():
        return {}
    try:
        return json.loads(REG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _shorten(text: str, limit: int = 320) -> str:
    text = " ".join(text.split())
    return text[: limit - 3] + "..." if len(text) > limit else text


@lru_cache(maxsize=1)
def _load_registry_links() -> Dict[str, str]:
    """
    check_turkish_law_registry.md içindeki tabloyu parse eder ve mevzuat no -> URL eşlemesi döner.
    """
    links: Dict[str, str] = {}
    if not REGISTRY_MD.exists():
        return links
    text = REGISTRY_MD.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) != 4:
            continue
        mevzuat_no, mevzuat_tur, tertip, _ = parts
        if not (mevzuat_no.isdigit() and mevzuat_tur.isdigit() and tertip.isdigit()):
            continue
        url = f"https://www.mevzuat.gov.tr/mevzuat?MevzuatNo={mevzuat_no}&MevzuatTur={mevzuat_tur}&MevzuatTertip={tertip}"
        links[mevzuat_no] = url
    return links


def find_articles(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Basit anahtar kelime/madde araması:
    - madde numarası geçiyorsa öncelik
    - query kelimeleri madde/paragraf metninde geçiyorsa ekle
    """
    data = _load_regulations()
    items: Dict[str, Dict] = data.get("items", {}) if isinstance(data, dict) else {}
    if not items:
        return []

    q = query.lower()
    tokens = [t for t in q.replace(",", " ").replace(".", " ").split() if len(t) > 3]

    results: List[Dict[str, str]] = []

    # Önce mevzuat no varsa doğrudan registry linkini ekle
    registry_links = _load_registry_links()
    for no, url in registry_links.items():
        if no in q:
            results.append(
                {
                    "ref": f"{no}",
                    "title": f"{no} Mevzuat Linki",
                    "text": url,
                    "score": 99,  # en üstte gelsin
                }
            )

    for code, item in items.items():
        for madde in item.get("maddeler", []):
            ref = madde.get("madde_no", "") or ""
            title = madde.get("baslik", "") or ""
            paragraphs = madde.get("paragraflar", []) or []
            para_text = " ".join((p or {}).get("metin", "") or "" for p in paragraphs)

            score = 0
            if ref and ref in q:
                score += 2
            if tokens and any(t in title.lower() for t in tokens if t):
                score += 1
            if tokens and any(t in para_text.lower() for t in tokens if t):
                score += 1
            if score == 0:
                continue

            results.append(
                {
                    "ref": f"{item.get('mevzuat_no','')}-{ref}".strip("-"),
                    "title": title.strip(),
                    "text": _shorten(para_text),
                    "score": score,
                }
            )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]
