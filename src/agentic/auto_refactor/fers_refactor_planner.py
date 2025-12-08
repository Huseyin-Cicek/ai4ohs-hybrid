import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from src.agentic.llama_learning_integration.llama_client import LlamaCPPError, llama_cpp

###############################################################################
#  SYSTEM CONFIG
###############################################################################

# Llama.cpp server context limit (server --ctx-size ile uyumlu)
CTX_LIMIT = 4096

# Fonksiyon ve dosya bazlı güvenli token limitleri
SAFE_FN_TOKEN_LIMIT = 1200
SAFE_FILE_TOKEN_LIMIT = 3000

# Çok büyük fonksiyonlar için chunk parametreleri
CHUNK_SIZE = 1000  # approx tokens per chunk
CHUNK_OVERLAP = 100

# Evrimsel hafıza dosyası
EVOLUTION_MEMORY_PATH = "logs/refactor/evolution_memory.json"
ROOT = Path(__file__).resolve().parents[3]


###############################################################################
#  HELPER FUNCTIONS
###############################################################################


def estimate_tokens(text: str) -> int:
    """Çok kaba bir token tahmini; Llama.cpp context sınırı için yeterli."""
    if not text:
        return 0
    # Ortalama 4 karakter ≈ 1 token varsayımı
    return max(1, len(text) // 4)


def chunk_text(text: str, size: int, overlap: int) -> List[str]:
    """Büyük fonksiyon gövdelerini Llama context sınırına göre parçalara böler."""
    chunks: List[str] = []
    if not text:
        return chunks

    step = max(1, size - overlap)
    for i in range(0, len(text), step):
        chunk = text[i : i + size]
        chunks.append(chunk)
        if i + size >= len(text):
            break
    return chunks


def parse_json_response(raw: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Llama.cpp cevabından JSON gövdesini ayıklar.
    Çözümlenemezse fallback döner.
    """
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return fallback
        return json.loads(raw[start : end + 1])
    except Exception:
        return fallback


###############################################################################
#  EVOLUTION MEMORY
###############################################################################


class EvolutionMemory:
    """
    Dosya/fonksiyon bazlı “geçmiş performans” bilgisini tutar.
    - success/fail sayıları
    - en son kullanılan mod
    Bu bilgiler ileride agresiflik seviyesini ayarlamak için kullanılabilir.
    """

    def __init__(self, path: str = EVOLUTION_MEMORY_PATH) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.data: Dict[str, Any] = {"files": {}, "functions": {}}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                # Bozulmuş dosya varsa sessizce sıfırdan başla
                self.data = {"files": {}, "functions": {}}

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            # Log yazılamasa bile ACE/FERS çalışmaya devam etmeli
            pass

    # -------- file-level helpers --------

    def _file_stats(self, rel: str) -> Dict[str, Any]:
        files = self.data.setdefault("files", {})
        if rel not in files:
            files[rel] = {"success": 0, "fail": 0, "last_mode": None}
        return files[rel]

    def record_file_pass(self, rel: str, mode: Optional[str] = None) -> None:
        stats = self._file_stats(rel)
        stats["success"] += 1
        if mode is not None:
            stats["last_mode"] = mode
        self.save()

    def record_file_fail(self, rel: str, reason: str) -> None:
        stats = self._file_stats(rel)
        stats["fail"] += 1
        stats["last_error"] = reason
        self.save()

    # -------- function-level helpers --------

    def record_function_skip(self, rel: str, fn_name: str, reason: str) -> None:
        funcs = self.data.setdefault("functions", {})
        key = f"{rel}::{fn_name}"
        rec = funcs.get(key, {"skips": 0})
        rec["skips"] = rec.get("skips", 0) + 1
        rec["last_reason"] = reason
        funcs[key] = rec
        self.save()


###############################################################################
#  MAIN PLANNER
###############################################################################


class FullEvolutionaryRefactorPlanner:
    """
    Full Evolutionary Refactor System (FERS)

    Özellikler:
    - Multi-file evolutionary refactor
    - Aggressive / Small Patch / Function-Or-Chunk modları
    - Llama.cpp tabanlı JSON patch üretimi (mümkün olduğunda)
    - Llama hatasında local minimal autopatch fallback
    - Context limit kontrolü (4096 ctx -> ~1200 güvenli fn token)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

        # Kaynak kök dizin; ACEExecutor genelde candidate path’i zaten “src/...” ile geçiriyor
        self.src_root = self.config.get("src_root", "")
        self.exclude_dirs = self.config.get(
            "exclude_dirs", ["tests", "__pycache__", "sandbox_repo"]
        )

        self.ctx_limit = int(self.config.get("ctx_limit", CTX_LIMIT))
        self.safe_fn_token_limit = int(self.config.get("safe_fn_token_limit", SAFE_FN_TOKEN_LIMIT))
        self.safe_file_token_limit = int(
            self.config.get("safe_file_token_limit", SAFE_FILE_TOKEN_LIMIT)
        )

        self.max_llama_tokens = int(self.config.get("max_llama_tokens", 800))
        self.memory = EvolutionMemory()

    # ------------------------------------------------------------------ utils

    def _normalize_candidate_files(
        self, candidate_files: Sequence[Union[str, Path, Dict[str, Any]]]
    ) -> List[str]:
        """
        ACE tarafı candidate_files’i farklı formatlarda geçebilir.
        Burada hepsini 'rel path string' haline getiriyoruz.
        """
        result: List[str] = []
        for item in candidate_files:
            rel: Optional[str] = None

            if isinstance(item, Path):
                rel = str(item).replace("\\", "/")
            elif isinstance(item, str):
                rel = item.replace("\\", "/")
            elif isinstance(item, dict):
                rel = (
                    item.get("rel")
                    or item.get("rel_path")
                    or item.get("path")
                    or item.get("file")
                    or item.get("relative_path")
                )
                if rel:
                    rel = str(rel).replace("\\", "/")

            if not rel:
                continue

            # Basit exclude kontrolü
            if any(part in rel.split("/") for part in self.exclude_dirs):
                continue

            result.append(rel)

        return result

    def _read_file(self, rel: str) -> Optional[str]:
        path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        if not path.exists() or not path.is_file():
            # src_root ayarlı ise onunla da dene
            if self.src_root:
                alt = Path(self.src_root) / rel
                if alt.exists() and alt.is_file():
                    path = alt
                else:
                    return None
            else:
                return None

        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="latin-1")
            except Exception:
                return None

    def _select_mode(self, tokens: int) -> str:
        """
        Token sayısına göre refactor modu seçimi.
        İleride EvolutionMemory verisiyle daha akıllı hale getirilebilir.
        """
        if tokens <= 600:
            return "AGGRESSIVE"
        if tokens <= self.safe_file_token_limit:
            return "SMALL_PATCH"
        return "FUNCTION_OR_CHUNK"

    # ---------------------------------------------------------------- Llama IO

    def _call_llama(self, prompt: str, n_predict: Optional[int] = None) -> str:
        """
        Llama.cpp ile konuşan ortak yardımcı.
        Hata durumunda LlamaCPPError fırlatır.
        """
        max_tokens = n_predict or self.max_llama_tokens
        return llama_cpp(prompt, n_predict=max_tokens)

    # ----------------------------------------------------------- full-file mode

    def _refactor_full_file(self, rel: str, content: str) -> Optional[Dict[str, str]]:
        """
        Tam dosya refactor denemesi.
        Llama hata verirse None, local fallback gerekirse minimal autopatch.
        Promptu basit tutuyoruz; JSON zorunluluğu yok, ama Llama’dan
        komple yeni dosya gövdesi bekliyoruz.
        """
        tokens = estimate_tokens(content)
        if tokens > self.safe_file_token_limit:
            return None

        prompt = (
            "You are an autonomous Python refactoring assistant.\n"
            "Refactor the following file to improve readability, maintainability,\n"
            "type hints, and basic PEP8 compliance. Keep behaviour the same.\n\n"
            f"FILE PATH: {rel}\n\n"
            "Return ONLY the full updated Python file, inside a ```python ... ``` block.\n\n"
            "-------- FILE START --------\n"
            f"{content}\n"
            "-------- FILE END ----------\n"
        )

        try:
            raw = self._call_llama(prompt)
        except LlamaCPPError as e:
            self.memory.record_file_fail(rel, f"llama_error:{e}")
            return None

        # Basit kod gövdeli çıkarma
        new_code = self._extract_code_block(raw)
        if not new_code or new_code.strip() == content.strip():
            return None

        return {"file": rel, "new_code": new_code}

    def _extract_code_block(self, raw: str) -> str:
        """
        Llama cevabından ```python ... ``` bloğunu çıkarır.
        Bulamazsa ham cevabı döner.
        """
        m = re.search(r"```python(.*)```", raw, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip("\n\r ")
        # Fallback: tüm cevabı dön (bazı modeller blok kullanmayabiliyor)
        return raw.strip("\n\r ")

    # -------------------------------------------------------- small patch mode

    def _refactor_small_patch(self, rel: str, content: str) -> Optional[Dict[str, str]]:
        """
        Küçük, düşük riskli değişiklikler.
        - Eksik module-level docstring ekleme
        - Basit type hint ekleme (sadece örnek)
        - Importları toparlama
        Llama çağrısı başarısız olursa lokal minimal autopatch’e düşer.
        """
        tokens = estimate_tokens(content)
        if tokens > self.safe_file_token_limit:
            # Bu durumda small patch'i tamamen lokal yapalım
            return self._minimal_autopatch(rel, content)

        prompt = (
            "You are a Python code quality assistant.\n"
            "Make a SMALL, SAFE improvement to the following file:\n"
            "- Add or improve module-level docstring if missing.\n"
            "- Add obvious type hints to simple functions if trivial.\n"
            "- Do NOT change business logic.\n"
            "- Keep the structure mostly the same.\n\n"
            f"FILE PATH: {rel}\n\n"
            "Return ONLY the full updated Python file, inside a ```python ... ``` block.\n\n"
            "-------- FILE START --------\n"
            f"{content}\n"
            "-------- FILE END ----------\n"
        )

        try:
            raw = self._call_llama(prompt, n_predict=600)
            new_code = self._extract_code_block(raw)
            if not new_code or new_code.strip() == content.strip():
                # Llama bir şey üretmediyse lokal minimal patch
                return self._minimal_autopatch(rel, content)
            return {"file": rel, "new_code": new_code}
        except LlamaCPPError:
            # Llama yoksa bile pipeline devam etsin
            return self._minimal_autopatch(rel, content)

    # --------------------------------------------------- function-or-chunk mode

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """
        Çok basit bir fonksiyon ayıklayıcı (def ... satırlarına göre).
        """
        pattern = re.compile(r"\ndef\s+([A-Za-z_][\w]*)\s*\(.*?\):", re.DOTALL)
        matches = list(pattern.finditer("\n" + content))

        funcs: List[Dict[str, Any]] = []
        for i, m in enumerate(matches):
            name = m.group(1)
            start = m.start(0)
            end = matches[i + 1].start(0) if i + 1 < len(matches) else len("\n" + content)
            body = ("\n" + content)[start:end]
            funcs.append({"name": name, "body": body, "start": start, "end": end})
        return funcs

    def _refactor_function_body(self, rel: str, fn_name: str, fn_body: str) -> Optional[str]:
        """
        Tek fonksiyon gövdesi üzerinde çalışır.
        """
        fn_tokens = estimate_tokens(fn_body)
        if fn_tokens > self.safe_fn_token_limit:
            self.memory.record_function_skip(rel, fn_name, f"too_large:{fn_tokens}")
            return None

        prompt = (
            "You are a Python refactoring assistant.\n"
            "Refactor ONLY the given function, keep the same signature and behaviour.\n"
            "Improve readability, add missing type hints, and basic PEP8.\n\n"
            f"FILE: {rel}\n"
            f"FUNCTION NAME: {fn_name}\n\n"
            "Return ONLY the updated function body, inside a ```python ... ``` block.\n\n"
            "-------- FUNCTION START --------\n"
            f"{fn_body}\n"
            "-------- FUNCTION END ----------\n"
        )

        try:
            raw = self._call_llama(prompt, n_predict=400)
            new_body = self._extract_code_block(raw)
            if not new_body or new_body.strip() == fn_body.strip():
                return None
            return new_body
        except LlamaCPPError:
            self.memory.record_function_skip(rel, fn_name, "llama_error")
            return None

    def _refactor_chunked_large_function(
        self, rel: str, fn_name: str, fn_body: str
    ) -> Optional[str]:
        """
        Çok büyük fonksiyonlar için chunk bazlı refactor.
        Burada sadece basit bir “dokunma” stratejisi kullanıyoruz:
        - Fonksiyonu parçala
        - Llama'ya küçük parçalar ver
        - Cevapları birleştir
        """
        chunks = chunk_text(fn_body, CHUNK_SIZE, CHUNK_OVERLAP)
        new_chunks: List[str] = []
        for idx, ch in enumerate(chunks):
            fn_tokens = estimate_tokens(ch)
            if fn_tokens > self.safe_fn_token_limit:
                # Bu chunk da çok büyükse, olduğu gibi bırak
                new_chunks.append(ch)
                continue

            prompt = (
                "You are a Python refactoring assistant.\n"
                "You will receive a CHUNK of a large function body.\n"
                "Make very small refactors (spacing, trivial hints), do NOT change logic.\n"
                "Return chunk inside ```python``` block.\n\n"
                f"FILE: {rel}\nFUNCTION: {fn_name}\nCHUNK INDEX: {idx}\n\n"
                "-------- CHUNK START --------\n"
                f"{ch}\n"
                "-------- CHUNK END ----------\n"
            )
            try:
                raw = self._call_llama(prompt, n_predict=400)
                new_chunks.append(self._extract_code_block(raw))
            except LlamaCPPError:
                new_chunks.append(ch)

        new_body = "".join(new_chunks)
        if new_body.strip() == fn_body.strip():
            return None
        return new_body

    # --------------------------------------------------------- minimal autopatch

    def _minimal_autopatch(self, rel: str, content: str) -> Dict[str, str]:
        """
        Llama hiç çalışmasa bile, her koşuda EN AZ bir küçük değişiklik
        üretmek için lokal “minimal patch”:
        - En üstte modül docstring yoksa ekler
        - Importları alfabetik sıraya sokar
        - Dosyanın sonunda tek newline olduğundan emin olur
        """
        new_content = content

        # 1) Module-level docstring
        stripped = new_content.lstrip()
        if not stripped.startswith('"""') and not stripped.startswith("'''"):
            new_content = f'"""Auto-refactored by ACE/FERS.\nThis module was touched by the evolutionary refactor pipeline.\n"""\n\n{new_content}'

        # 2) Importları toparla
        lines = new_content.splitlines()
        imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
        other: List[str] = []
        for l in lines:
            if l.startswith("import ") or l.startswith("from "):
                continue
            other.append(l)
        if imports:
            sorted_imports = sorted(set(imports))
            new_content = "\n".join(sorted_imports + [""] + other)

        # 3) Dosya sonu newline
        if not new_content.endswith("\n"):
            new_content += "\n"

        return {"file": rel, "new_code": new_content}

    # ------------------------------------------------------------ public API ---

    def plan_evolution(
        self, candidate_files: Sequence[Union[str, Path, Dict[str, Any]]]
    ) -> List[Dict[str, str]]:
        """
        ACEExecutor tarafından çağrılan ana giriş noktası.

        Parametre:
            candidate_files: ACE’in seçtiği dosya listesi
                             (str, Path veya {rel/path/file: ...} dict olabilir)

        Dönüş:
            List[{"file": <relative_path>, "new_code": <updated_source>}]
        """
        rel_files = self._normalize_candidate_files(candidate_files)
        print(f"[FERS] Selected {len(rel_files)} files for evolutionary pass.")

        patches: List[Dict[str, str]] = []

        for rel in rel_files:
            content = self._read_file(rel)
            if not content:
                self.memory.record_file_fail(rel, "no_content")
                continue

            tokens = estimate_tokens(content)
            mode = self._select_mode(tokens)
            print(f"[FERS] File={rel} tokens={tokens} -> Mode={mode}")

            try:
                patch: Optional[Dict[str, str]] = None

                if mode == "AGGRESSIVE":
                    patch = self._refactor_full_file(rel, content)
                    if patch is None:
                        # Full file çalışmazsa small patch'e düş
                        patch = self._refactor_small_patch(rel, content)

                elif mode == "SMALL_PATCH":
                    patch = self._refactor_small_patch(rel, content)

                else:  # FUNCTION_OR_CHUNK
                    funcs = self._extract_functions(content)
                    if not funcs:
                        patch = self._minimal_autopatch(rel, content)
                    else:
                        updated = "\n" + content
                        changed = False
                        for fn in funcs[:3]:  # ilk birkaç fonksiyonla sınırlı
                            name = fn["name"]
                            body = fn["body"]
                            fn_tokens = estimate_tokens(body)

                            if fn_tokens <= self.safe_fn_token_limit:
                                new_body = self._refactor_function_body(rel, name, body)
                            else:
                                new_body = self._refactor_chunked_large_function(rel, name, body)

                            if new_body:
                                start = fn["start"]
                                end = fn["end"]
                                updated = updated[:start] + "\n" + new_body + "\n" + updated[end:]
                                changed = True

                        if changed and updated.strip() != content.strip():
                            # Baştaki \n'i temizle
                            updated = updated.lstrip("\n")
                            patch = {"file": rel, "new_code": updated}
                        else:
                            patch = self._minimal_autopatch(rel, content)

                if patch:
                    patches.append(patch)
                    self.memory.record_file_pass(rel, mode=mode)
                else:
                    # Yine de minimal autopatch ile dokun
                    fallback = self._minimal_autopatch(rel, content)
                    patches.append(fallback)
                    self.memory.record_file_pass(rel, mode="MINIMAL")

            except Exception as e:  # ACE çökmesin
                print(f"[FERS][ERROR] planning {rel}: {e}")
                self.memory.record_file_fail(rel, f"exception:{e}")

        print(f"[FERS] Total patches produced: {len(patches)}")
        return patches

    # Eski arayüzü kullanan kodlar için geriye dönük uyumluluk:
    def generate_refactor_plan(self) -> Dict[str, Any]:
        """
        Eski tek-parametresiz arayüz; tüm src ağacını tarar.
        Yeni ACE entegrasyonu için plan_evolution kullanılıyor.
        """
        # src içindeki tüm .py dosyalarını topla
        base = Path(self.src_root) if self.src_root else Path("src")
        candidate_files: List[str] = []
        for root, dirs, files in os.walk(base):
            # exclude_dirs
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            for f in files:
                if not f.endswith(".py"):
                    continue
                p = Path(root) / f
                rel = str(p.relative_to(Path("."))).replace("\\", "/")
                candidate_files.append(rel)

        patches = self.plan_evolution(candidate_files)
        return {"patches": patches}

    def _load_ref_report(self):
        ref_report_path = ROOT / "logs" / "workspace-ref-report.json"
        if not ref_report_path.exists():
            return None
        with ref_report_path.open("r", encoding="utf8") as f:
            return json.load(f)

    def _assign_evolution_weights(self, files):
        """
        workspace_ref_integrity raporuna göre dosya ağırlıklarını ayarlar.
        - candidate_integrate: agresif refactor (2.0)
        - candidate_prune: düşük öncelik (0.5)
        - diğerleri: 1.0
        """
        ref_report = self._load_ref_report() or {}
        integrate = {c["path"] for c in ref_report.get("candidate_integrate", [])}
        prune = {c["path"] for c in ref_report.get("candidate_prune", [])}

        weighted = []
        for f in files:
            rel = f.get("rel_path") or f.get("path") or f.get("file") or ""
            if not rel:
                continue
            if rel in integrate:
                weight = 2.0  # Aggressive evolution: mutlaka patch
            elif rel in prune:
                weight = 0.5  # Daha az öncelik, ama soft-deprecation üret
            else:
                weight = 1.0
            f["evolution_weight"] = weight
            weighted.append(f)
        return weighted
