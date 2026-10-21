import io, os, sys, time, unittest, json
os.environ["SECRET_KEY"] = "test-secret-key-0123456789"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import auth, llm
from app.ingest.parser import extract_text
from app.audit.engine import run_audit

class T(unittest.TestCase):
    def test_password_and_token(self):
        h = auth.hash_password("rahasia-kuat-123")
        self.assertTrue(auth.verify_password("rahasia-kuat-123", h)); self.assertFalse(auth.verify_password("salah", h))
        t = auth.make_token(7, "reviewer"); self.assertEqual(auth.read_token(t)["sub"], 7)
        with self.assertRaises(ValueError): auth.read_token(t[:-3] + "xyz")
        with self.assertRaises(ValueError): auth.read_token(auth.make_token(1, "admin", ttl=-5))

    def test_llm_validation(self):
        text = "KESATU : Dinas Kesehatan bekerja sama dan berbagi data pasien dengan PT Maju.\nKEDUA : Biaya ditanggung daerah."
        fake = lambda s, u: "```json\n" + json.dumps({
            "facts": {"berbagi_data_pasien": {"value": True, "evidence": "berbagi data pasien dengan PT Maju", "confidence": 0.9},
                      "layanan_klinis": {"value": True, "evidence": "kutipan yang tidak ada di dokumen"},
                      "kunci_ngawur": {"value": True, "evidence": "Biaya ditanggung daerah"}},
            "clause_notes": [{"clause": "KESATU", "issue": "Dasar hukum data tidak ada", "severity": "K", "quote": "berbagi data pasien dengan PT Maju",
                              "suggestion": "Tambah dasar", "legal_refs": ["UU 17/2023", "UU 99/2099"]},
                             {"clause": "KEDUA", "issue": "x", "quote": "kalimat karangan", "suggestion": "y"}]}) + "\n```"
        r = llm.review(text, "pks", ["UU 17/2023"], call=fake)
        self.assertEqual(list(r["facts"]), ["berbagi_data_pasien"])          # bukti palsu & kunci asing dibuang
        self.assertEqual(len(r["clause_notes"]), 1)                          # kutipan karangan dibuang
        st = {x["ref"]: x["status"] for x in r["clause_notes"][0]["legal_refs"]}
        self.assertEqual(st["UU 17/2023"], "ada_di_basis_terverifikasi"); self.assertEqual(st["UU 99/2099"], "belum_terverifikasi")
        self.assertIn("error", llm.review(text, "pks", [], call=lambda s, u: "bukan json"))

    def test_scanned_pdf_fallback(self):
        from pypdf import PdfWriter
        w = PdfWriter(); w.add_blank_page(width=200, height=200); b = io.BytesIO(); w.write(b)
        r = extract_text("scan.pdf", b.getvalue())
        self.assertIn("ocr_used", r)
        if not r["ocr_used"]: self.assertTrue(r["needs_ocr"]); self.assertTrue(r["ocr_note"])

    def test_engine_still_works(self):
        self.assertEqual(run_audit("kepbup", {"memuat_norma_umum": True})["status"], "Tidak layak diproses")

if __name__ == "__main__":
    unittest.main(verbosity=2)
