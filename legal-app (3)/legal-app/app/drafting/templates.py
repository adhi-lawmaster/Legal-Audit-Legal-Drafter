"""Generator draf. Isian kosong menjadi penanda [ISI: ...]; dasar hukum bawaan diberi [VERIFIKASI]."""
import re

COMMON = [("kabupaten", "Nama Kabupaten", 0), ("nomor", "Nomor", 0), ("tahun", "Tahun", 0), ("tentang", "Tentang / Judul", 0)]
FIELDS = {
 "perda": COMMON + [("filosofis", "Pertimbangan filosofis", 1), ("sosiologis", "Pertimbangan sosiologis", 1),
    ("yuridis", "Pertimbangan yuridis", 1), ("dasar_hukum_tambahan", "Dasar hukum tambahan (satu per baris)", 1),
    ("definisi", "Definisi (istilah = pengertian, satu per baris)", 1), ("materi_pokok", "Materi pokok (satu pasal per baris)", 1)],
 "perbup": COMMON + [("pertimbangan", "Pertimbangan", 1), ("perda_induk", "Perda yang dijabarkan (judul, nomor, tahun)", 0),
    ("pasal_delegasi", "Pasal Perda yang mendelegasikan", 0), ("dasar_hukum_tambahan", "Dasar hukum tambahan (satu per baris)", 1),
    ("materi_pokok", "Materi pokok (satu pasal per baris)", 1)],
 "kepbup": COMMON + [("pertimbangan", "Pertimbangan", 1), ("dasar_hukum_tambahan", "Dasar hukum tambahan (satu per baris)", 1),
    ("diktum", "Diktum (satu per baris: KESATU, KEDUA, ...)", 1)],
 "mou": [("pihak_1", "Pihak Pertama", 0), ("pihak_2", "Pihak Kedua", 0), ("tentang", "Tentang", 0), ("nomor", "Nomor", 0),
    ("maksud", "Maksud dan tujuan", 1), ("ruang_lingkup", "Ruang lingkup (satu per baris)", 1), ("jangka_waktu", "Jangka waktu", 0),
    ("tempat", "Tempat penandatanganan", 0), ("tanggal", "Tanggal", 0)],
 "pks": [("pihak_1", "Pihak Pertama", 0), ("pihak_2", "Pihak Kedua", 0), ("tentang", "Tentang", 0), ("nomor", "Nomor", 0),
    ("dasar_kesepakatan", "Dasar (MoU/kesepakatan induk, bila ada)", 0), ("objek", "Objek/ruang lingkup (satu per baris)", 1),
    ("hak_kewajiban_1", "Hak & kewajiban Pihak Pertama (satu per baris)", 1), ("hak_kewajiban_2", "Hak & kewajiban Pihak Kedua (satu per baris)", 1),
    ("pembiayaan", "Pembiayaan dan sumber dana", 1), ("jangka_waktu", "Jangka waktu", 0),
    ("tempat", "Tempat penandatanganan", 0), ("tanggal", "Tanggal", 0)],
}
BASE_LAW = {
 "perda": ["Pasal 18 ayat (6) UUD 1945", "Undang-Undang Nomor 23 Tahun 2014 tentang Pemerintahan Daerah", "Undang-Undang Nomor 17 Tahun 2023 tentang Kesehatan"],
 "perbup": ["Undang-Undang Nomor 23 Tahun 2014 tentang Pemerintahan Daerah", "Undang-Undang Nomor 17 Tahun 2023 tentang Kesehatan"],
 "kepbup": ["Undang-Undang Nomor 23 Tahun 2014 tentang Pemerintahan Daerah", "Undang-Undang Nomor 30 Tahun 2014 tentang Administrasi Pemerintahan"],
}
ORD = ["KESATU", "KEDUA", "KETIGA", "KEEMPAT", "KELIMA", "KEENAM", "KETUJUH", "KEDELAPAN", "KESEMBILAN", "KESEPULUH"]

def _g(v, k, label=None):
    x = (v.get(k) or "").strip()
    return x if x else f"[ISI: {label or k}]"

def _lines(v, k, label):
    x = [l.strip() for l in (v.get(k) or "").splitlines() if l.strip()]
    return x or [f"[ISI: {label}]"]

class _B:
    def __init__(self): self.out, self.n = [], 0
    def add(self, kind, text): self.out.append((kind, text))
    def pasal(self, *paras):
        self.n += 1; self.add("center", f"Pasal {self.n}")
        for p in paras: self.add("p", p)

def _opening(b, kind, v, jabatan_title):
    b.add("title", f"{kind} {_g(v,'kabupaten','kabupaten').upper()}")
    b.add("title", f"NOMOR {_g(v,'nomor')} TAHUN {_g(v,'tahun')}")
    b.add("title", f"TENTANG {_g(v,'tentang').upper()}")
    b.add("center", "DENGAN RAHMAT TUHAN YANG MAHA ESA")
    b.add("center", f"BUPATI {_g(v,'kabupaten','kabupaten').upper()},")

def _mengingat(b, inst, v):
    b.add("p", "Mengingat:")
    laws = [f"{l} [VERIFIKASI]" for l in BASE_LAW[inst]] + _lines(v, "dasar_hukum_tambahan", "dasar hukum tambahan")
    for i, l in enumerate(laws, 1): b.add("item", f"{i}. {l};")

def build(inst, v):
    b = _B()
    if inst == "perda":
        _opening(b, "PERATURAN DAERAH KABUPATEN", v, "")
        b.add("p", "Menimbang:")
        for a, k, lab in (("a", "filosofis", "pertimbangan filosofis"), ("b", "sosiologis", "pertimbangan sosiologis"), ("c", "yuridis", "pertimbangan yuridis")):
            b.add("item", f"{a}. bahwa {_g(v,k,lab)};")
        b.add("item", f"d. bahwa berdasarkan pertimbangan sebagaimana dimaksud dalam huruf a, huruf b, dan huruf c, perlu membentuk Peraturan Daerah tentang {_g(v,'tentang')};")
        _mengingat(b, inst, v)
        b.add("center", "Dengan Persetujuan Bersama\nDEWAN PERWAKILAN RAKYAT DAERAH KABUPATEN dan BUPATI\nMEMUTUSKAN:")
        b.add("p", f"Menetapkan: PERATURAN DAERAH TENTANG {_g(v,'tentang').upper()}.")
        b.add("center", "BAB I KETENTUAN UMUM")
        b.pasal("Dalam Peraturan Daerah ini yang dimaksud dengan:", *[f"{i}. {d}" for i, d in enumerate(_lines(v, "definisi", "definisi"), 1)])
        b.add("center", "BAB II MAKSUD, TUJUAN, DAN RUANG LINGKUP")
        b.pasal("[ISI: maksud dan tujuan]"); b.pasal("[ISI: ruang lingkup]")
        b.add("center", "BAB III MATERI POKOK")
        for l in _lines(v, "materi_pokok", "materi pokok"): b.pasal(l)
        b.add("center", "BAB IV PEMBIAYAAN"); b.pasal("Pembiayaan pelaksanaan Peraturan Daerah ini bersumber dari [ISI: sumber dana].")
        b.add("center", "BAB V KETENTUAN PERALIHAN DAN PENUTUP")
        b.pasal("Ketentuan lebih lanjut mengenai pelaksanaan Peraturan Daerah ini diatur dengan Peraturan Bupati.")
        b.pasal("Peraturan Daerah ini mulai berlaku pada tanggal diundangkan.", "Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Daerah ini dengan penempatannya dalam Lembaran Daerah Kabupaten.")
    elif inst == "perbup":
        _opening(b, "PERATURAN BUPATI", v, "")
        b.add("p", "Menimbang:")
        b.add("item", f"a. bahwa {_g(v,'pertimbangan')};")
        b.add("item", f"b. bahwa untuk melaksanakan ketentuan {_g(v,'pasal_delegasi','pasal delegasi')} {_g(v,'perda_induk','Perda induk')}, perlu menetapkan Peraturan Bupati tentang {_g(v,'tentang')};")
        _mengingat(b, inst, v)
        b.add("p", "MEMUTUSKAN:")
        b.add("p", f"Menetapkan: PERATURAN BUPATI TENTANG {_g(v,'tentang').upper()}.")
        b.add("center", "BAB I KETENTUAN UMUM"); b.pasal("[ISI: definisi]")
        b.add("center", "BAB II MATERI POKOK")
        for l in _lines(v, "materi_pokok", "materi pokok"): b.pasal(l)
        b.add("center", "BAB III KETENTUAN PENUTUP")
        b.pasal("Peraturan Bupati ini mulai berlaku pada tanggal diundangkan.", "Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Bupati ini dengan penempatannya dalam Berita Daerah Kabupaten.")
    elif inst == "kepbup":
        _opening(b, "KEPUTUSAN BUPATI", v, "")
        b.add("p", "Menimbang:"); b.add("item", f"a. bahwa {_g(v,'pertimbangan')};")
        _mengingat(b, inst, v)
        b.add("p", "MEMUTUSKAN:")
        b.add("p", f"Menetapkan: KEPUTUSAN BUPATI TENTANG {_g(v,'tentang').upper()}.")
        for i, d in enumerate(_lines(v, "diktum", "diktum")): b.add("p", f"{ORD[min(i, 9)]} : {d}")
        b.add("p", "Keputusan Bupati ini mulai berlaku pada tanggal ditetapkan.")
    elif inst in ("mou", "pks"):
        pks = inst == "pks"
        b.add("title", "PERJANJIAN KERJA SAMA" if pks else "KESEPAKATAN BERSAMA (NOTA KESEPAHAMAN)")
        b.add("title", f"ANTARA {_g(v,'pihak_1').upper()} DAN {_g(v,'pihak_2').upper()}")
        b.add("title", f"TENTANG {_g(v,'tentang').upper()}"); b.add("center", f"Nomor: {_g(v,'nomor')}")
        b.add("p", f"Pada hari ini, tanggal {_g(v,'tanggal')}, bertempat di {_g(v,'tempat')}, para pihak: (1) {_g(v,'pihak_1')}, selanjutnya disebut PIHAK PERTAMA; dan (2) {_g(v,'pihak_2')}, selanjutnya disebut PIHAK KEDUA. Penandatangan bertindak berdasarkan [ISI: dasar kewenangan/surat kuasa].")
        if pks and v.get("dasar_kesepakatan", "").strip(): b.add("p", f"Perjanjian ini merupakan tindak lanjut dari {v['dasar_kesepakatan'].strip()}.")
        b.pasal("[ISI: maksud dan tujuan]" if not pks else "Perjanjian ini bertujuan [ISI: tujuan].")
        b.pasal("Ruang lingkup:", *[f"{i}. {l}" for i, l in enumerate(_lines(v, "ruang_lingkup" if not pks else "objek", "ruang lingkup"), 1)])
        if pks:
            b.pasal("Hak dan kewajiban PIHAK PERTAMA:", *_lines(v, "hak_kewajiban_1", "hak & kewajiban pihak pertama"))
            b.pasal("Hak dan kewajiban PIHAK KEDUA:", *_lines(v, "hak_kewajiban_2", "hak & kewajiban pihak kedua"))
            b.pasal("Pembiayaan:", _g(v, "pembiayaan", "pembiayaan"), "Kewajiban pembayaran daerah hanya berlaku sepanjang tersedia dalam APBD dan/atau telah memperoleh persetujuan yang dipersyaratkan.")
            b.pasal("Pengelolaan data dan kerahasiaan: para pihak menjaga kerahasiaan data, termasuk data pasien dan rekam medis, sesuai peraturan perundang-undangan; penggunaan data dibatasi pada tujuan perjanjian ini.")
            b.pasal("Pemantauan dan pelaporan: [ISI: mekanisme monitoring dan pelaporan].")
            b.pasal("Wanprestasi dan sanksi: [ISI: ketentuan wanprestasi yang proporsional].")
            b.pasal("Keadaan kahar (termasuk wabah/KLB): para pihak dibebaskan dari tanggung jawab atas keterlambatan atau kegagalan akibat keadaan kahar yang diberitahukan secara tertulis.")
            b.pasal("Penyelesaian perselisihan: diselesaikan secara musyawarah; apabila tidak tercapai, melalui [ISI: mekanisme yang sah].")
        b.pasal(f"Jangka waktu: {_g(v,'jangka_waktu')}; dapat diperpanjang atau diakhiri berdasarkan kesepakatan tertulis para pihak.")
        if pks: b.pasal("Perubahan dilakukan dengan addendum tertulis yang ditandatangani para pihak.")
        b.pasal("Perjanjian ini dibuat rangkap [ISI: jumlah] bermeterai cukup, masing-masing berkekuatan hukum yang sama.")
        b.add("center", "PIHAK PERTAMA, [ISI: nama/jabatan]          PIHAK KEDUA, [ISI: nama/jabatan]")
    else:
        raise ValueError("Instrumen tidak dikenal")
    missing = sorted(set(re.findall(r"\[ISI: [^\]]+\]", "\n".join(t for _, t in b.out))))
    unverified = sum(t.count("[VERIFIKASI]") for _, t in b.out)
    return {"paragraphs": b.out, "missing": missing, "unverified_citations": unverified}

def to_docx(result) -> bytes:
    import io, docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH as A
    d = docx.Document()
    for kind, text in result["paragraphs"]:
        p = d.add_paragraph(text)
        if kind in ("title", "center"):
            p.alignment = A.CENTER
            for r in p.runs: r.bold = kind == "title" or text.startswith(("Pasal", "BAB"))
        elif kind == "item": p.paragraph_format.left_indent = docx.shared.Cm(1)
    bio = io.BytesIO(); d.save(bio); return bio.getvalue()
