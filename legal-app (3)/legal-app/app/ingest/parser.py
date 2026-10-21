import io

MAX_BYTES = 20 * 1024 * 1024

def extract_text(filename: str, data: bytes) -> dict:
    if len(data) > MAX_BYTES:
        raise ValueError("Ukuran file melebihi 20 MB.")
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in reader.pages]
        text, n_pages = "\n".join(pages), len(pages)
    elif ext == "docx":
        import docx
        d = docx.Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        text, n_pages = "\n".join(parts), None
    else:
        raise ValueError("Format tidak didukung. Gunakan .pdf atau .docx (simpan .doc sebagai .docx).")
    # PDF hasil scan hampir tidak punya teks -> perlu OCR (belum diimplementasikan)
    needs_ocr = ext == "pdf" and len(text.strip()) < 80 * max(n_pages or 1, 1)
    ocr_used, ocr_note = False, None
    if needs_ocr:
        from ..ocr import ocr_pdf
        ocr_text, ocr_note = ocr_pdf(data)
        if ocr_text and ocr_text.strip():
            text, ocr_used, needs_ocr = ocr_text, True, False
    return {"text": text, "pages": n_pages, "needs_ocr": needs_ocr, "ocr_used": ocr_used, "ocr_note": ocr_note}
