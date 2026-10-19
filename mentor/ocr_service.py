"""
OCR Service for MentoraX AI.

Uses pytesseract (Tesseract 4) to extract text from a marksheet image,
then parses the raw text to find:
  - marks_obtained  (e.g. "72", "72/100", "Marks: 72")
  - total_marks     (e.g. from "72/100" or "Total: 100")
  - student_id      (e.g. "STU2024001", "Roll No: 101")
  - subject_name    (e.g. "Mathematics", "Subject: Physics")

Call: extract_from_image(image_file)  -> dict
"""

import re
import logging
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)

# Common subject keywords to detect
SUBJECT_KEYWORDS = [
    "mathematics", "math", "maths",
    "physics", "chemistry", "biology",
    "english", "hindi", "history",
    "geography", "economics", "computer",
    "science", "accounts", "commerce",
    "statistics", "calculus", "algebra",
]


def extract_from_image(image_file) -> dict:
    """
    Main entry point.
    Accepts a Django InMemoryUploadedFile or any file-like object.
    Returns a dict:
        {
            "success": bool,
            "marks_obtained": float or None,
            "total_marks":    float or None,
            "student_id":     str   or None,
            "subject_name":   str   or None,
            "raw_text":       str,            # full OCR output (for debug)
            "error":          str,            # non-empty only on failure
        }
    """
    try:
        import pytesseract
    except ImportError:
        return _fail("pytesseract not installed. Run: pip install pytesseract")

    try:
        img = Image.open(image_file)
        img = _preprocess(img)
        raw_text = pytesseract.image_to_string(img, config="--psm 6")
    except Exception as e:
        logger.error("OCR extraction error: %s", e)
        return _fail(f"Could not read image: {e}")

    parsed = _parse(raw_text)
    parsed["raw_text"] = raw_text
    parsed["success"] = any([
        parsed["marks_obtained"],
        parsed["total_marks"],
        parsed["student_id"],
        parsed["subject_name"],
    ])
    parsed["error"] = "" if parsed["success"] else (
        "Could not extract data automatically. Please fill in the fields manually."
    )
    return parsed


# ─── Image pre-processing ────────────────────────────────────────────────────

def _preprocess(img: Image.Image) -> Image.Image:
    """Convert to greyscale, sharpen, and boost contrast for better OCR accuracy."""
    img = img.convert("L")                          # greyscale
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.0)  # boost contrast
    return img


# ─── Text parsing ────────────────────────────────────────────────────────────

def _parse(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    result = {
        "marks_obtained": None,
        "total_marks":    None,
        "student_id":     None,
        "subject_name":   None,
    }

    for line in lines:
        low = line.lower()

        # ── Marks: "72/100" or "72 / 100" ──────────────────
        m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", line)
        if m and result["marks_obtained"] is None:
            obtained = float(m.group(1))
            total = float(m.group(2))
            if obtained <= total and total > 0:
                result["marks_obtained"] = obtained
                result["total_marks"] = total
                continue

        # ── "Marks Obtained: 72" or "Marks: 72" ────────────
        m = re.search(r"marks?\s*(?:obtained)?\s*[:\-]?\s*(\d+(?:\.\d+)?)", low)
        if m and result["marks_obtained"] is None:
            result["marks_obtained"] = float(m.group(1))

        # ── "Total Marks: 100" or "Out of: 100" ────────────
        m = re.search(r"(?:total|max(?:imum)?|out\s*of)\s*(?:marks?)?\s*[:\-]?\s*(\d+(?:\.\d+)?)", low)
        if m and result["total_marks"] is None:
            result["total_marks"] = float(m.group(1))

        # ── Score/Grade: "Score: 72" ────────────────────────
        m = re.search(r"(?:score|obtained|secured)\s*[:\-]?\s*(\d+(?:\.\d+)?)", low)
        if m and result["marks_obtained"] is None:
            result["marks_obtained"] = float(m.group(1))

        # ── Student ID: "STU2024001", "Roll No: 101" ────────
        m = re.search(r"(?:roll\s*no\.?|student\s*id|reg(?:istration)?\s*(?:no\.?|number)?)\s*[:\-]?\s*([A-Za-z0-9\-]+)", low)
        if m and result["student_id"] is None:
            result["student_id"] = m.group(1).upper()

        if result["student_id"] is None:
            # raw alphanumeric ID pattern e.g. STU2024001, 21CS101
            m = re.search(r"\b([A-Za-z]{2,4}\d{4,10}|\d{2}[A-Za-z]{2}\d{3,6})\b", line)
            if m:
                result["student_id"] = m.group(1).upper()

        # ── Subject name ─────────────────────────────────────
        if result["subject_name"] is None:
            m = re.search(r"(?:subject|paper|course)\s*[:\-]?\s*([A-Za-z ]+)", low)
            if m:
                candidate = m.group(1).strip().title()
                if len(candidate) > 2:
                    result["subject_name"] = candidate
            else:
                # Check if any line contains a known subject keyword
                for kw in SUBJECT_KEYWORDS:
                    if kw in low:
                        result["subject_name"] = kw.title()
                        break

    return result


def _fail(msg: str) -> dict:
    return {
        "success": False,
        "marks_obtained": None,
        "total_marks":    None,
        "student_id":     None,
        "subject_name":   None,
        "raw_text":       "",
        "error":          msg,
    }
