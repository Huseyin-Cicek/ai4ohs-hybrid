"""
Prompt templates used by ACE / FERS refactor planners.
These templates generate Llama.cpp-friendly JSON patch outputs.
"""

# ---------------------------------------------------------------------
# FULL FILE PATCH PROMPT (AGGRESSIVE / SMALL_PATCH / FALLBACK)
# Llama.cpp bu prompt ile dosya seviyesinde tam patch üretir.
# ---------------------------------------------------------------------
PATCH_PROMPT = """
You are an AI code refactoring system. Your task is to rewrite the following file.
Respond ONLY with a JSON object using this schema:

{
  "file": "<relative path>",
  "patch": "<unified diff patch>"
}

Rules:
- Maintain original functionality unless unsafe.
- Improve formatting, clarity, type hints, and structure.
- NEVER add explanations.
- NEVER wrap output in Markdown.
- ALWAYS return valid JSON only.

FILE TO REWRITE:
----------------
{file_content}
----------------
"""


# ---------------------------------------------------------------------
# FUNCTION-LEVEL PATCH PROMPT
# Fonksiyon bazlı çalışma: kısa context ile güvenli refactor
# ---------------------------------------------------------------------
FUNCTION_PATCH_PROMPT = """
You are an AI refactoring assistant. Rewrite ONLY the function body below.
Respond ONLY with plain Python function body (no JSON, no markdown).

Function name: {func_name}

Original function body:
-----------------------
{func_body}
-----------------------

Rules:
- Preserve logical behavior.
- Improve readability & formatting.
- Add missing type hints where obvious.
- Remove redundant or dead code.
- Keep imports untouched.
- NO explanations.
- NO extra comments.
- NO markdown.

Return ONLY the rewritten function body.
"""


# ---------------------------------------------------------------------
# MINIMAL PATCH PROMPT
# "Small Patch Mode" — Her zaman bir değişiklik üretmek için.
# ---------------------------------------------------------------------
MINIMAL_PATCH_PROMPT = """
You must produce a minimal but meaningful improvement to this file.
Do NOT leave the file unchanged.

Examples of allowed improvements:
- Add or fix docstrings
- Add type annotations
- Improve formatting (PEP8)
- Rename unclear variable names
- Add safe defensive checks

Respond ONLY with a unified diff patch in JSON:

{
  "file": "<relative path>",
  "patch": "<unified diff>"
}

FILE CONTENT:
-------------
{file_content}
-------------
"""


# ---------------------------------------------------------------------
# FALLBACK SAFE PATCH PROMPT
# Refactor mümkün olmadığında en küçük güvenli değişiklik yapılır.
# ---------------------------------------------------------------------
SAFE_FALLBACK_PATCH_PROMPT = """
The previous refactor attempt failed. Produce a small, guaranteed-safe patch.
DO NOT modify logic. Only cosmetic improvements allowed.

Return JSON with unified diff only:

{
  "file": "<relative path>",
  "patch": "<unified diff>"
}

CONTENT:
--------
{file_content}
--------
"""
