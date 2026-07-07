import io
import logging

import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes

logger = logging.getLogger("airdos.ocr")


def extract_text_from_bytes(file_bytes: bytes, content_type: str | None, filename: str) -> str:
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return _extract_from_pdf(file_bytes)
    return _extract_from_image(file_bytes)


def _extract_from_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    return pytesseract.image_to_string(
        image,
        lang="eng+rus+kaz",
        config="--psm 6",
    )


def _extract_from_pdf(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(pdf_bytes, dpi=200)
    texts = []
    for idx, image in enumerate(images):
        logger.info("OCR processing PDF page %s", idx + 1)
        text = pytesseract.image_to_string(
            image,
            lang="eng+rus+kaz",
            config="--psm 6",
        )
        texts.append(text)
    return "\n".join(texts)
