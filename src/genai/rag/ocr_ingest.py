"""
OCR Ingest Helper
-----------------

Ekran görüntüsü / imaj dosyalarını OCR ile metne çevirir ve chunk'lara böler.
"""

from pathlib import Path
from typing import List

try:
    import pytesseract
    from PIL import Image
except ImportError as exc:  # pragma: no cover - ortam bağımlılığı
    pytesseract = None
    Image = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from genai.rag.chunker import apply_rules


SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


class OCRUnavailable(RuntimeError):
    """Tesseract/Pillow eksik olduğunda fırlatılır."""


def ocr_image_to_text(image_path: str) -> str:
    """
    Tek bir imajı OCR ile metne çevirir.
    """

    if pytesseract is None or Image is None:
        raise OCRUnavailable(
            f"pytesseract/Pillow gerekli ancak eksik: {_IMPORT_ERROR!s if _IMPORT_ERROR else ''}"
        )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXT:
        raise ValueError(f"Unsupported image format: {path.suffix}")

    img = Image.open(path)
    return pytesseract.image_to_string(img)


def ingest_image_to_chunks(image_path: str, doc_type: str = "general") -> List[str]:
    """
    OCR -> chunk sürecini tek adımda çalıştırır.
    """

    text = ocr_image_to_text(image_path)
    return apply_rules(text, doc_type=doc_type)
