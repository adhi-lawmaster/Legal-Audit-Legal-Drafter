import re
from sqlalchemy.orm import Session
from .. import models

LEVELS = {"undang-undang": "UU", "peraturan pemerintah": "PP", "peraturan presiden": "Perpres",
          "peraturan menteri": "Permen", "peraturan daerah": "Perda", "peraturan bupati": "Perbup"}
PAT = re.compile(r"(Undang-Undang|Peraturan Pemerintah|Peraturan Presiden|Peraturan Menteri [A-Za-z ]{0,40}?"
                 r"|Peraturan Daerah[A-Za-z ]{0,30}?|Peraturan Bupati[A-Za-z ]{0,30}?)\s+(?:Republik Indonesia\s+)?"
                 r"Nomor\s+(\d+)\s+Tahun\s+(\d{4})", re.I)

def check_citations(text: str, db: Session) -> list[dict]:
    seen, res = set(), []
    for m in PAT.finditer(text):
        key = next((v for k, v in LEVELS.items() if m.group(1).lower().startswith(k)), "?")
        ident = (key, m.group(2), int(m.group(3)))
        if ident in seen:
            continue
        seen.add(ident)
        n = (db.query(models.Norma).filter_by(level=key, nomor=m.group(2), tahun=int(m.group(3))).first())
        status = ("tidak_ada_di_basis_pengetahuan" if not n else
                  "dicabut_atau_diubah" if n.status != "berlaku" else
                  "berlaku_terverifikasi" if n.verified else "ada_belum_diverifikasi")
        res.append({"rujukan": f"{key} {m.group(2)}/{m.group(3)}", "status": status})
    return res
