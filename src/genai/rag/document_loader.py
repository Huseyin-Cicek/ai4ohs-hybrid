import os
try:
    import markdownify  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    markdownify = None
try:
    import mammoth  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mammoth = None
try:
    from pdfminer.high_level import extract_text  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    extract_text = None

from genai.rag.ocr_ingest import ocr_image_to_text

"""
AI4OHS-HYBRID - Document Loader v2.1
HSSE mevzuat, ESS dokümanları, ISO maddeleri, saha raporları ve ekran görüntüleri için loader.
"""


def load_document(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()

    if ext in {".txt", ".md"}:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    if ext == ".pdf":
        if extract_text is None:
            raise RuntimeError("pdfminer.six dependency missing for PDF extraction.")
        return extract_text(filepath)

    if ext in {".docx", ".doc"}:
        if mammoth is None or markdownify is None:
            raise RuntimeError("mammoth/markdownify dependencies missing for doc/docx conversion.")
        with open(filepath, "rb") as f:
            result = mammoth.convert_to_html(f)
            return markdownify.markdownify(result.value)

    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        return ocr_image_to_text(filepath)

    return ""
