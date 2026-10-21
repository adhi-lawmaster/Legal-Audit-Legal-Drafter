import re

ORD = r"KESATU|KEDUA|KETIGA|KEEMPAT|KELIMA|KEENAM|KETUJUH|KEDELAPAN|KESEMBILAN|KESEPULUH"
HEAD = re.compile(rf"^\s*(?:(Pasal\s+\d+[A-Z]?)\s*$|(BAB\s+[IVXLC]+)\b.*$|({ORD})\s*:)", re.I)

def segment(text: str) -> list[dict]:
    """Pecah dokumen menjadi unit: Pasal / BAB / diktum KESATU dst. Sisanya masuk 'pembukaan'."""
    clauses, cur = [], {"number": "Pembukaan", "heading": "", "lines": []}
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            clauses.append(cur)
            num = next(g for g in m.groups() if g)
            cur = {"number": re.sub(r"\s+", " ", num).strip(), "heading": "", "lines": [line.strip()]}
        else:
            cur["lines"].append(line.strip())
    clauses.append(cur)
    return [{"number": c["number"], "text": "\n".join(l for l in c["lines"] if l).strip()}
            for c in clauses if any(c["lines"])]
