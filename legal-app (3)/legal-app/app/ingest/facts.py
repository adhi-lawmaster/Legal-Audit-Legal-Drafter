import re

TITLES = [("perda", r"PERATURAN DAERAH"), ("perbup", r"PERATURAN BUPATI"),
          ("kepbup", r"KEPUTUSAN BUPATI"), ("pks", r"PERJANJIAN KERJA SAMA"),
          ("mou", r"NOTA KESEPAHAMAN|MEMORANDUM OF UNDERSTANDING|KESEPAKATAN BERSAMA|\bMOU\b")]

def guess_instrument(text: str):
    head = text[:1500].upper()
    for inst, pat in TITLES:
        if re.search(pat, head):
            return inst
    return None

# fakta -> pola. Hanya mendeteksi KEBERADAAN teks; hasilnya SARAN yang wajib dikonfirmasi pengguna.
POSITIVE = {
    "memuat_sanksi_pidana": r"ketentuan pidana|dipidana|pidana kurungan|denda paling banyak",
    "memuat_pungutan": r"retribusi|pajak daerah",
    "memuat_pungutan_baru": r"retribusi|pajak daerah",
    "berbagi_data_pasien": r"data pasien|rekam medis|data kesehatan",
    "memanfaatkan_aset_daerah": r"barang milik daerah|aset daerah|pemanfaatan (?:gedung|lahan|tanah)",
    "layanan_klinis": r"pelayanan kesehatan|layanan klinis|tindakan medis",
    "memuat_kewajiban_mengikat": r"wajib membayar|ganti rugi|denda|sanksi",
    "ada_naskah_akademik": r"naskah akademik",
    "persetujuan_dprd": r"persetujuan (?:dewan perwakilan rakyat daerah|dprd)",
}
# Fakta yang bisa disimpulkan dari ketiadaan teks pada dokumen penuh (PKS)
ABSENCE_FALSE = {"ada_keadaan_kahar": r"keadaan kahar|force majeure|keadaan memaksa"}

def suggest_facts(text: str, instrument: str | None) -> dict:
    out = {}
    for fact, pat in POSITIVE.items():
        m = re.search(pat, text, re.I)
        if m:
            s = max(0, m.start() - 60)
            out[fact] = {"value": True, "evidence": text[s:m.end() + 60].replace("\n", " ")}
    if instrument == "pks":
        for fact, pat in ABSENCE_FALSE.items():
            m = re.search(pat, text, re.I)
            out[fact] = ({"value": True, "evidence": text[max(0, m.start()-40):m.end()+40].replace("\n", " ")}
                         if m else {"value": False, "evidence": "Frasa tidak ditemukan di dokumen."})
    return out
