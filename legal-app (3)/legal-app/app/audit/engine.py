import pathlib
import yaml

RULES_FILE = pathlib.Path(__file__).parent.parent / "rules" / "rules.yaml"
_DATA = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
RULES, RULES_VERSION = _DATA["rules"], str(_DATA["version"])
SEV = {"K": 5, "T": 4, "S": 3, "R": 1}
WEIGHT = {"kewenangan": 1.5, "hierarki": 1.5, "prosedur": 1.2,
          "keuangan": 1.3, "teknis": 1.0, "redaksional": 0.5}

def _eval(c: dict, f: dict):
    """True / False / None (None = fakta belum dijawab)."""
    if "all" in c:
        r = [_eval(x, f) for x in c["all"]]
        return False if any(x is False for x in r) else (None if None in r else True)
    if "any" in c:
        r = [_eval(x, f) for x in c["any"]]
        return True if any(x is True for x in r) else (None if None in r else False)
    v = f.get(c["fact"])
    return None if v is None else v == c["is"]

def run_audit(instrument: str, facts: dict) -> dict:
    findings = []
    for r in RULES:
        if instrument not in r["applies_to"]:
            continue
        res = _eval(r["fail_if"], facts)
        if res is False:
            continue
        certainty = 1.0 if res else 0.5
        findings.append({
            "id": r["id"], "severity": r["severity"], "category": r["category"],
            "title": r["title"], "advice": r["advice"], "basis": r.get("basis", ""),
            "state": "terpenuhi_masalah" if res else "belum_terjawab",
            "score": round(SEV[r["severity"]] * certainty * WEIGHT[r["category"]], 2),
        })
    findings.sort(key=lambda x: x["score"], reverse=True)
    confirmed = [x for x in findings if x["state"] == "terpenuhi_masalah"]
    sevs = {x["severity"] for x in confirmed}
    status = ("Tidak layak diproses" if "K" in sevs else
              "Perlu perbaikan" if "T" in sevs else
              "Layak dengan catatan" if sevs else
              "Tidak ada temuan terkonfirmasi" if not findings else "Lengkapi jawaban checklist")
    top = [x["score"] for x in findings[:5]]
    total = round(0.6 * (top[0] if top else 0) + 0.4 * (sum(top) / len(top) if top else 0), 2)
    return {"status": status, "score": total, "findings": findings,
            "rules_version": RULES_VERSION,
            "catatan": "Alat bantu telaah. Wajib direview Bagian Hukum; dasar hukum diverifikasi ke sumber resmi."}
