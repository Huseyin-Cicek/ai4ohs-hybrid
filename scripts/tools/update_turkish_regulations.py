#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI4OHS-HYBRID – Turkish Regulations Harvester (Full-Text v3.1.2)"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

DEFAULT_INPUT = Path("./docs/check-turkish-law.md")
DEFAULT_OUTPUT = Path("./docs/turkish_regulations.json")
BASE = "https://www.mevzuat.gov.tr"


@dataclass
class MevzuatRow:
    mevzuat_no: str
    mevzuat_tur: str
    mevzuat_tertip: str
    mevzuat_adi: str

    @property
    def key(self) -> str:
        return f"{self.mevzuat_no}-{self.mevzuat_tur}-{self.mevzuat_tertip}"

    @property
    def url(self) -> str:
        return f"{BASE}/mevzuat?MevzuatNo={self.mevzuat_no}&MevzuatTur={self.mevzuat_tur}&MevzuatTertip={self.mevzuat_tertip}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_table(md_path: Path) -> List["MevzuatRow"]:
    text = md_path.read_text(encoding="utf-8")
    rows = []
    in_table = False
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        if re.fullmatch(r"\|\s*-{3,}.*\|", line):
            in_table = True
            continue
        if not in_table:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        mevzuat_no, mevzuat_tur, mevzuat_tertip, mevzuat_adi = parts[:4]
        if mevzuat_no.lower() in {"mevzuatno", "no"}:
            continue
        rows.append(MevzuatRow(str(mevzuat_no), str(mevzuat_tur), str(mevzuat_tertip), mevzuat_adi))
    return rows


def load_state(path: Path) -> Dict:
    if not path.exists():
        return {"last_run": None, "registry_size": 0, "items": {}, "search_index": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "items" not in data or not isinstance(data["items"], dict):
            data["items"] = {}
        if "search_index" not in data or not isinstance(data["search_index"], dict):
            data["search_index"] = {}
        return data
    except json.JSONDecodeError:
        backup = path.with_suffix(".corrupt")
        path.rename(backup)
        return {
            "last_run": None,
            "registry_size": 0,
            "items": {},
            "search_index": {},
            "warning": f"Corrupt JSON moved to {backup.name}",
        }


def store_state(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


_TURKISH_ENCODINGS = ["utf-8", "cp1254", "iso-8859-9"]


def _count_repl(s: str) -> int:
    return s.count("\ufffd") or s.count("�")


def smart_decode(content: bytes, content_type: str, header_charset: Optional[str]) -> str:
    tried = []
    if header_charset:
        try:
            txt = content.decode(header_charset, errors="strict")
            return unicodedata.normalize("NFC", txt)
        except Exception as e:
            tried.append(("header", header_charset, str(e)))
    candidates = []
    for enc in _TURKISH_ENCODINGS:
        try:
            txt = content.decode(enc, errors="strict")
            txt = unicodedata.normalize("NFC", txt)
            candidates.append((enc, txt, _count_repl(txt)))
        except Exception:
            pass
    if not candidates:
        for enc in _TURKISH_ENCODINGS:
            try:
                txt = content.decode(enc, errors="replace")
                txt = unicodedata.normalize("NFC", txt)
                candidates.append((enc, txt, _count_repl(txt)))
            except Exception:
                pass
    if not candidates:
        txt = content.decode("utf-8", errors="replace")
        return unicodedata.normalize("NFC", txt)

    def score(cand):
        enc, txt, repl = cand
        has_tr = bool(re.search(r"[çğıöşüÇĞİÖŞÜ]", txt))
        return (repl, 0 if has_tr else 1, 0 if enc != "utf-8" else 1)

    enc, txt, _ = sorted(candidates, key=score)[0]
    return txt


def http_get(url: str, timeout: float) -> Dict:
    try:
        resp = httpx.get(
            url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "ai4ohs-hybrid/1.3"}
        )
        ct = resp.headers.get("Content-Type", "")
        charset = None
        m = re.search(r"charset\s*=\s*([A-Za-z0-9_\-]+)", ct or "", flags=re.I)
        if m:
            charset = m.group(1).lower()
        html = ""
        if (
            "text/html" in ct
            or "application/xhtml" in ct
            or ct == ""
            or resp.url.path.lower().endswith((".htm", ".html"))
        ):
            html = smart_decode(resp.content, ct, charset)
        return {
            "status": "ok",
            "final_url": str(resp.url),
            "content_type": ct,
            "html": html,
            "bytes": resp.content,
            "hash": hashlib.sha256(resp.content).hexdigest(),
            "code": resp.status_code,
        }
    except httpx.HTTPError as e:
        return {
            "status": "error",
            "error": str(e),
            "final_url": url,
            "content_type": "",
            "html": "",
            "bytes": b"",
            "hash": "",
            "code": 0,
        }


CAND_SUBSTR = (
    "MevzuatMetin",
    "mevzuatmetin",
    "Metin",
    "metin",
    "Icerik",
    "icerik",
    "Content",
    "govde",
)


def discover_content_urls(main_html: str, main_url: str, row: MevzuatRow) -> List[str]:
    soup = BeautifulSoup(main_html or "", "html.parser")
    cands = []
    for ifr in soup.find_all("iframe"):
        src = ifr.get("src", "")
        if any(s in src for s in CAND_SUBSTR):
            cands.append(urljoin(main_url, src))
    for a in soup.find_all("a"):
        href = a.get("href", "")
        txt = a.get_text(" ", strip=True).lower()
        if (
            any(s.lower() in href for s in CAND_SUBSTR)
            or "metin" in txt
            or "içerik" in txt
            or "icerik" in txt
        ):
            cands.append(urljoin(main_url, href))
    base = [
        f"{BASE}/MevzuatMetin/{row.mevzuat_tur}.{row.mevzuat_tertip}.{row.mevzuat_no}",
        f"{BASE}/MevzuatMetin/{row.mevzuat_tur}.{row.mevzuat_tertip}.{row.mevzuat_no}.html",
        f"{BASE}/MevzuatMetin/{row.mevzuat_tur}.{row.mevzuat_tertip}.{row.mevzuat_no}.htm",
        f"{BASE}/Metin/{row.mevzuat_tur}.{row.mevzuat_tertip}.{row.mevzuat_no}.html",
        f"{BASE}/Metin/{row.mevzuat_tur}.{row.mevzuat_tertip}.{row.mevzuat_no}.htm",
    ]
    seen = set()
    uniq = []
    for u in list(cands) + base:
        if u and u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def html_to_text(soup: BeautifulSoup) -> str:
    for bad in soup(["script", "style", "noscript"]):
        bad.decompose()
    candidates = []
    for id_ in [
        "icerik",
        "content",
        "divContent",
        "main",
        "form1",
        "ctl00_MCPH1_pnlIcerik",
        "metin",
        "govde",
    ]:
        el = soup.find(id=id_)
        if el:
            candidates.append(el)
    for cls in ["icerik", "content", "metin", "maddegovde", "govde", "yazi"]:
        el = soup.find(class_=cls)
        if el:
            candidates.append(el)
    node = candidates[0] if candidates else (soup.body or soup)
    text = node.get_text("\n", strip=True)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\xa0", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text


MADDE_HDR = re.compile(r"(?:(?<=\n)|^)\s*(MADDE)\s+(\d+[A-Z]?)\s*[–\-—:]?\s*", flags=re.IGNORECASE)
PARAGRAPH_HDR = re.compile(r"(?:(?<=\n)|^)\s*\((\d+)\)\s*")
BENT_HDR = re.compile(r"(?:(?<=\n)|^)\s*([a-zçğıöşü])\)\s*", flags=re.IGNORECASE)


def split_by(regex, text: str):
    items = []
    last_end = 0
    last_key = None
    for m in regex.finditer(text):
        start = m.start()
        if last_key is not None:
            items.append((last_key, text[last_end:start].strip()))
        key = m.group(m.lastindex or 1)
        last_key = key
        last_end = m.end()
    if last_key is not None:
        items.append((last_key, text[last_end:].strip()))
    return items


def parse_full_text(html: str) -> Dict:
    soup = BeautifulSoup(html or "", "html.parser")
    text = html_to_text(soup)
    articles_out = []
    flat_index = {}
    madde_blocks = split_by(MADDE_HDR, text)
    for madde_no, madde_chunk in madde_blocks:
        article = {"madde_no": str(madde_no), "baslik": None, "paragraflar": []}
        first_line = madde_chunk.split("\n", 1)[0].strip()
        if " (1)" not in first_line:
            maybe = first_line.split(".")[0]
            if 2 < len(maybe) < 160:
                article["baslik"] = maybe
        para_blocks = split_by(PARAGRAPH_HDR, madde_chunk) or [("1", madde_chunk)]
        for p_no, p_chunk in para_blocks:
            parag = {"no": str(p_no), "metin": None, "bentler": []}
            m = BENT_HDR.search(p_chunk)
            if m:
                if m.start() > 0:
                    parag["metin"] = p_chunk[: m.start()].strip() or None
                for b_no, b_txt in split_by(BENT_HDR, p_chunk):
                    bkey = b_no.lower()
                    btext = b_txt.strip()
                    parag["bentler"].append({"no": bkey, "metin": btext})
                    flat_index[f"MADDE {article['madde_no']}/{parag['no']}-{bkey}"] = btext
            else:
                parag["metin"] = p_chunk.strip()
                flat_index[f"MADDE {article['madde_no']}/{parag['no']}"] = parag["metin"]
            article["paragraflar"].append(parag)
        articles_out.append(article)
    return {"articles": articles_out, "flat": flat_index}


def update_item(state: Dict, row: MevzuatRow, timeout: float, full: bool) -> None:
    key = row.key
    url = row.url
    now = _utc_now()
    items = state.setdefault("items", {})
    search_index = state.setdefault("search_index", {})
    item = items.setdefault(key, {})
    item.update(
        {
            "mevzuat_no": row.mevzuat_no,
            "mevzuat_tur": row.mevzuat_tur,
            "mevzuat_tertip": row.mevzuat_tertip,
            "mevzuat_adi": row.mevzuat_adi,
            "url": url,
            "last_checked": now,
            "status": item.get("status", "unknown"),
        }
    )
    item.setdefault("last_changed", now)
    item.setdefault("content_hash", None)
    item.setdefault("final_url", None)
    item.setdefault("meta", {})
    item.setdefault("maddeler", [])
    item.setdefault("maddeler_flat", [])
    item.setdefault("debug", {}).setdefault("tried_urls", [])
    main = http_get(url, timeout)
    item["debug"]["tried_urls"].append(
        {
            "url": url,
            "status": main.get("status"),
            "code": main.get("code"),
            "ct": main.get("content_type"),
        }
    )
    candidates = discover_content_urls(
        main.get("html", "") or "", main.get("final_url") or url, row
    ) or discover_content_urls("", url, row)
    used_html = ""
    used_url = main.get("final_url") or url
    used_from = "landing"
    if "MADDE" in (main.get("html") or "") or "Madde" in (main.get("html") or ""):
        used_html = main.get("html") or ""
    else:
        for cand in candidates:
            r = http_get(cand, timeout)
            item["debug"]["tried_urls"].append(
                {
                    "url": cand,
                    "status": r.get("status"),
                    "code": r.get("code"),
                    "ct": r.get("content_type"),
                }
            )
            if r["status"] != "ok":
                continue
            ct = r.get("content_type", "")
            h = r.get("html") or ""
            if "text/html" in ct or "application/xhtml" in ct or ct == "":
                if ("MADDE" in h) or ("Madde" in h):
                    used_url, used_html, used_from = r.get("final_url"), h, "probe"
                    break
    if not used_html:
        used_html = main.get("html") or ""
        used_url = main.get("final_url") or url
        used_from = "fallback"
    content_bytes = (used_html or "").encode("utf-8", errors="ignore")
    new_hash = hashlib.sha256(content_bytes).hexdigest()
    if item.get("content_hash") != new_hash:
        item["last_changed"] = now
        item["content_hash"] = new_hash
    item["final_url"] = used_url
    item["status"] = "ok"
    item["debug"]["used_from"] = used_from
    if full and used_html:
        parsed = parse_full_text(used_html)
        item["maddeler"] = parsed["articles"]
        flat_list = [{"ref": ref, "text": text} for ref, text in parsed["flat"].items()]

        def _sort_key(_ref: str):
            m = re.match(r"^MADDE\s+(\d+)[A-Z]?/(\d+)(?:-([a-zçğıöşü]))?$", _ref, flags=re.I)
            if not m:
                return (10**9, 10**9, "zzz")
            art = int(m.group(1))
            par = int(m.group(2))
            bent = m.group(3) or ""
            return (art, par, bent)

        flat_list.sort(key=lambda x: _sort_key(x["ref"]))
        item["maddeler_flat"] = flat_list
        for ref, text in parsed["flat"].items():
            search_index[f"{key}::{ref}"] = {"key": key, "ref": ref, "text": text}


def main() -> None:
    p = argparse.ArgumentParser(
        description="Update Turkish regulations registry from mevzuat.gov.tr"
    )
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--only", nargs="*")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--full", action="store_true")
    a = p.parse_args()
    rows = [r for r in read_table(a.input) if r.mevzuat_no and r.mevzuat_no.lower() != "tbd"]
    if a.only:
        wanted = set(a.only)
        rows = [r for r in rows if r.mevzuat_no in wanted]
    state = load_state(a.output)
    for row in rows:
        update_item(state, row, timeout=a.timeout, full=a.full)
    state["last_run"] = _utc_now()
    state["registry_size"] = len(rows)
    store_state(a.output, state)


if __name__ == "__main__":
    main()
