import json
import os
import re
from typing import Dict, List, Optional, Set

from agentic.llama_learning_integration.llama_client import LlamaCPPError, llama_cpp

LLAMA_SYSTEM_PROMPT_FULL_FILE = """
You are an autonomous code-refactoring engine.

Task:
- Receive a single Python file.
- Rewrite the FULL file with cleaner, safer, more maintainable code.
- Keep public API (function names, signatures) compatible unless obviously wrong.
- Do NOT add business logic, only improve structure, readability and robustness.
- You must ALWAYS return ONLY valid JSON.

RESPONSE FORMAT (MANDATORY):

{
  "patches": [
    {
      "new_code": "<FULL UPDATED FILE CONTENT AS PYTHON CODE>"
    }
  ]
}

RULES:
- Do NOT include backticks.
- Do NOT include commentary or explanations outside JSON.
- "patches" MUST exist (can be empty list).
- "new_code" MUST contain the FULL file content (not a diff).
- If no improvement is needed, return: {"patches": []}
"""

LLAMA_SYSTEM_PROMPT_FUNCTION = """
You are an autonomous Python refactoring assistant.

Task:
- You will receive a SINGLE Python function (including its full definition).
- Improve ONLY this function: readability, robustness, clear docstring, better typing.
- Do NOT change the function name or parameters unless obviously buggy.
- Do NOT add side effects or new dependencies.
- You must ALWAYS return ONLY valid JSON.

RESPONSE FORMAT (MANDATORY):

{
  "patches": [
    {
      "function_name": "<EXACT FUNCTION NAME>",
      "new_body": "<FULL FUNCTION DEFINITION INCLUDING SIGNATURE AND BODY>"
    }
  ]
}

RULES:
- Do NOT include backticks.
- Do NOT include commentary or explanations outside JSON.
- "patches" MUST exist (can be empty list).
- "new_body" MUST contain the FULL function definition (def ...).
- If no improvement is needed, return: {"patches": []}
"""


class RefactorPlannerLlama:
    """
    Multi-file, token-aware, function-level incremental refactor planner.
    """

    def __init__(
        self,
        include_dirs: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        max_file_size_kb: int = 200,
        max_files_per_run: int = 10,
        max_est_tokens_per_file: int = 3000,
        max_functions_per_large_file: int = 3,
        enable_test_aware_prioritization: bool = True,
    ):
        self.src_root = "src"
        self.include_dirs = include_dirs or []
        self.exclude_dirs = exclude_dirs or ["__pycache__", "tests", "sandbox_repo"]
        self.max_size_bytes = max_file_size_kb * 1024
        self.max_files_per_run = max_files_per_run
        self.max_est_tokens_per_file = max_est_tokens_per_file
        self.max_functions_per_large_file = max_functions_per_large_file
        self.enable_test_aware = enable_test_aware_prioritization

    # ---------------------- complexity & tokens -------------------------
    def _estimate_tokens(self, text: str) -> int:
        return max(1, int(len(text) / 4))

    def _compute_complexity(self, content: str) -> int:
        lines = content.count("\n") + 1
        funcs = content.count("def ")
        classes = content.count("class ")
        branches = sum(
            content.count(k) for k in [" if ", " for ", " while ", " try:", " except ", " with "]
        )
        return lines + 3 * funcs + 4 * classes + 2 * branches

    # ---------------------- test-aware hints ----------------------------
    def _load_test_failure_hints(self) -> Set[str]:
        hints: Set[str] = set()
        if not self.enable_test_aware:
            return hints

        candidate_files = [
            os.path.join("logs", "tests", "last_pytest_output.txt"),
            os.path.join("logs", "tests", "last_failed_modules.txt"),
        ]
        for path in candidate_files:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                for m in re.findall(r"([\w/\\]+\.py)", text):
                    hints.add(m.replace("\\", "/"))
            except Exception:
                continue
        return hints

    # ---------------------- file scanning & batching --------------------
    def _scan_python_files(self) -> List[Dict]:
        files: List[Dict] = []

        for root, dirs, filenames in os.walk(self.src_root):
            if any(ex in root for ex in self.exclude_dirs):
                continue

            if self.include_dirs:
                if not any(os.path.join(self.src_root, inc) in root for inc in self.include_dirs):
                    continue

            for f in filenames:
                if not f.endswith(".py"):
                    continue

                abs_path = os.path.join(root, f)
                size = os.path.getsize(abs_path)

                rel_path = abs_path.replace(self.src_root + os.sep, "").replace("\\", "/")

                with open(abs_path, "r", encoding="utf-8") as fh:
                    content = fh.read()

                complexity = self._compute_complexity(content)
                est_tokens = self._estimate_tokens(content)

                files.append(
                    {
                        "abs": abs_path,
                        "rel": rel_path,
                        "size": size,
                        "complexity": complexity,
                        "est_tokens": est_tokens,
                        "content": content,
                    }
                )

        failure_hints = self._load_test_failure_hints()

        def priority_key(info: Dict):
            rel = info["rel"]
            hinted = any(h in rel or rel in h for h in failure_hints)
            test_boost = -1000 if hinted else 0
            return (test_boost, -info["complexity"], info["size"])

        files.sort(key=priority_key)
        return files

    # ---------------------- prompt builders -----------------------------
    def _build_full_file_prompt(self, rel_path: str, content: str) -> str:
        return f"""{LLAMA_SYSTEM_PROMPT_FULL_FILE}

FILE PATH:
{rel_path}

SOURCE CODE:
----------------
{content}
----------------
"""

    def _build_function_prompt(self, rel_path: str, func_name: str, func_body: str) -> str:
        return f"""{LLAMA_SYSTEM_PROMPT_FUNCTION}

FILE PATH:
{rel_path}

FUNCTION NAME:
{func_name}

FUNCTION DEFINITION:
----------------
{func_body}
----------------
"""

    # ---------------------- JSON parse ----------------------------------
    def _parse_json_response(self, text: str) -> Dict:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                return {"patches": []}
            data = json.loads(text[start : end + 1])
            patches = data.get("patches", [])
            if not isinstance(patches, list):
                patches = []
            return {"patches": patches}
        except Exception:
            return {"patches": []}

    # ---------------------- function extraction -------------------------
    def _extract_functions(self, content: str) -> List[Dict]:
        pattern = re.compile(r"\ndef\s+([a-zA-Z_][\w]*)\s*\(.*?\):", re.DOTALL)
        matches = list(pattern.finditer("\n" + content))

        funcs: List[Dict] = []
        for i, m in enumerate(matches):
            name = m.group(1)
            start = m.start(0)
            end = matches[i + 1].start(0) if i + 1 < len(matches) else len("\n" + content)
            body = ("\n" + content)[start:end]
            funcs.append(
                {
                    "name": name,
                    "body": body,
                    "start": start,
                    "end": end,
                }
            )
        return funcs

    def _apply_function_patches_to_content(self, content: str, func_patches: List[Dict]) -> str:
        if not func_patches:
            return content

        text = "\n" + content
        for patch in func_patches:
            name = patch.get("function_name")
            new_body = patch.get("new_body")
            if not name or not new_body:
                continue

            pattern = re.compile(rf"\ndef\s+{re.escape(name)}\s*\(.*?\):", re.DOTALL)
            m = pattern.search(text)
            if not m:
                continue
            start = m.start(0)
            m2 = pattern.search(text, m.end(0))
            end = m2.start(0) if m2 else len(text)

            text = text[:start] + "\n" + new_body.strip("\n") + "\n" + text[end:]

        return text.lstrip("\n")

    # ---------------------- MAIN: ACE çağrısı ---------------------------
    def generate_refactor_plan(self) -> Dict:
        file_infos = self._scan_python_files()
        all_patches: List[Dict] = []

        if not file_infos:
            return {"patches": []}

        selected_files = file_infos[: self.max_files_per_run]

        print(f"[Planner] {len(selected_files)} dosya bu koşuda refactor edilecek.")

        for info in selected_files:
            rel = info["rel"]
            content = info["content"]
            est_tokens = info["est_tokens"]

            # FULL FILE
            if est_tokens <= self.max_est_tokens_per_file:
                prompt = self._build_full_file_prompt(rel, content)
                try:
                    raw = llama_cpp(prompt, n_predict=min(1024, self.max_est_tokens_per_file * 2))
                except LlamaCPPError as e:
                    print(f"[Planner] Llama error on file {rel}: {e}")
                    continue

                parsed = self._parse_json_response(raw)
                patches = parsed.get("patches", [])

                for p in patches:
                    if not isinstance(p, dict):
                        continue
                    new_code = p.get("new_code")
                    if not isinstance(new_code, str):
                        continue
                    all_patches.append(
                        {
                            "file": f"{self.src_root}/{rel}",
                            "new_code": new_code,
                        }
                    )
            else:
                # FUNCTION-LEVEL
                funcs = self._extract_functions(content)
                funcs_sorted = sorted(funcs, key=lambda x: len(x["body"]), reverse=True)
                target_funcs = funcs_sorted[: self.max_functions_per_large_file]

                func_patches: List[Dict] = []
                for fn in target_funcs:
                    # === BURADA TOKEN LİMİT KONTROLÜ EKLENDİ ===
                    fn_tokens = self._estimate_tokens(fn["body"])

                    # 4096 ctx size → güvenli token limiti yaklaşık 1200
                    if fn_tokens > 1200:
                        print(
                            f"[Planner] Skip function {fn['name']} in {rel}: "
                            f"too large for Llama context (est_tokens={fn_tokens})"
                        )
                        continue

                    prompt = self._build_function_prompt(rel, fn["name"], fn["body"])
                    try:
                        raw = llama_cpp(prompt, n_predict=512)
                    except LlamaCPPError as e:
                        print(f"[Planner] Llama error on function {fn['name']} in {rel}: {e}")
                        continue

                    parsed = self._parse_json_response(raw)
                    patches = parsed.get("patches", [])
                    for p in patches:
                        if not isinstance(p, dict):
                            continue
                        if p.get("function_name") != fn["name"]:
                            continue
                        if "new_body" not in p or not isinstance(p["new_body"], str):
                            continue
                        func_patches.append(p)

                new_full_content = self._apply_function_patches_to_content(content, func_patches)

                if new_full_content != content:
                    all_patches.append(
                        {
                            "file": f"{self.src_root}/{rel}",
                            "new_code": new_full_content,
                        }
                    )

        print(f"[Planner] Üretilen toplam patch sayısı: {len(all_patches)}")
        return {"patches": all_patches}
