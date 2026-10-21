"""OCR untuk PDF hasil scan. Perlu paket tesseract-ocr (+ bahasa 'ind') terpasang di server."""
def available() -> bool:
    try:
        import pytesseract, pypdfium2  # noqa
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def ocr_pdf(data: bytes, lang: str = "ind+eng", max_pages: int = 80):
    """Return (teks atau None, catatan)."""
    try:
        import pypdfium2 as pdfium, pytesseract
        pytesseract.get_tesseract_version()
    except Exception as e:
        return None, f"OCR tidak tersedia di server ({type(e).__name__}). Pasang tesseract-ocr dan paket Python OCR."
    pdf = pdfium.PdfDocument(data)
    n = min(len(pdf), max_pages)
    out = [pytesseract.image_to_string(pdf[i].render(scale=2).to_pil(), lang=lang) for i in range(n)]
    note = "Teks dari OCR: periksa manual nomor pasal, angka, dan tanggal."
    if len(pdf) > n:
        note += f" Hanya {n} dari {len(pdf)} halaman diproses."
    return "\n".join(out), note
