import io
import logging

import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes

logger = logging.getLogger("airdos.ocr")

MAX_IMAGE_WIDTH = 2000
OCR_CONFIG = "--psm 6 --oem 1 -c tessedit_do_invert=0"


def extract_text_from_bytes(file_bytes: bytes, content_type: str | None, filename: str) -> str:
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return _extract_from_pdf(file_bytes)
    return _extract_from_image(file_bytes)


def _prepare_image(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image = image.convert("L")

    width, height = image.size
    if width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / width
        new_height = int(height * ratio)
        image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)

    return image


def _extract_from_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    image = _prepare_image(image)

    return pytesseract.image_to_string(
        image,
        lang="eng+rus+kaz",
        config=OCR_CONFIG,
    )


def _extract_from_pdf(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(pdf_bytes, dpi=150, fmt="jpeg", first_page=1, last_page=1)
    if not images:
        return ""

    image = images[0]
    image = _prepare_image(image)
    logger.info("OCR processing first PDF page")
    return pytesseract.image_to_string(
        image,
        lang="eng+rus+kaz",
        config=OCR_CONFIG,
    )
