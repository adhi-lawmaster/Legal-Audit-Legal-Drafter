import hashlib, os, pathlib, time
from collections import defaultdict
from fastapi import FastAPI, Depends, Response, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal
from . import models, schemas, auth, llm, ocr
from .drafting import templates as tpl
from .ingest.parser import extract_text
from .ingest.segment import segment
from .ingest.facts import guess_instrument, suggest_facts
from .ingest.citations import check_citations
from .audit.classify import classify_instrument
from .audit.engine import run_audit, RULES, RULES_VERSION

auth.ensure_secret()
Base.metadata.create_all(engine)
app = FastAPI(title="Legal Audit & Drafting - Dinkes")
bearer = HTTPBearer(auto_error=False)
ANY = ("admin", "reviewer", "penyusun")
FAILS: dict[str, list[float]] = defaultdict(list)

@app.on_event("startup")
def bootstrap():
    with SessionLocal() as db:
        if db.query(models.User).count() == 0:
            u, p = os.getenv("ADMIN_USER", "admin"), os.getenv("ADMIN_PASSWORD", "")
            if len(p) < 10:
                raise RuntimeError("Isi ADMIN_PASSWORD (minimal 10 karakter) untuk membuat admin pertama.")
            db.add(models.User(username=u, password_hash=auth.hash_password(p), role="admin")); db.commit()

def current_user(creds=Depends(bearer), db: Session = Depends(get_db)):
    if not creds:
        raise HTTPException(401, "Perlu login")
    try:
        claims = auth.read_token(creds.credentials)
    except ValueError:
        raise HTTPException(401, "Sesi tidak valid atau kedaluwarsa")
    u = db.get(models.User, int(claims["sub"]))
    if not u or not u.active:
        raise HTTPException(401, "Akun tidak aktif")
    return u

def require(*roles):
    def dep(u=Depends(current_user)):
        if u.role not in roles:
            raise HTTPException(403, "Peran tidak diizinkan")
        return u
    return dep

def log(db, u, action, target=""):
    db.add(models.ActivityLog(user=u.username, action=action, target=str(target)[:120]))

def can_see(u, owner_id):
    return u.role in ("admin", "reviewer") or owner_id == u.id

# ---------- auth & pengguna
@app.post("/auth/login")
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    now = time.time()
    FAILS[body.username] = [t for t in FAILS[body.username] if now - t < 300]
    if len(FAILS[body.username]) >= 5:
        raise HTTPException(429, "Terlalu banyak percobaan. Coba lagi beberapa menit.")
    u = db.query(models.User).filter_by(username=body.username).first()
    if not u or not u.active or not auth.verify_password(body.password, u.password_hash):
        FAILS[body.username].append(now)
        raise HTTPException(401, "Username atau password salah")
    db.add(models.ActivityLog(user=u.username, action="login")); db.commit()
    return {"token": auth.make_token(u.id, u.role), "role": u.role}

@app.get("/me")
def me(u=Depends(current_user)):
    return {"username": u.username, "role": u.role, "llm_enabled": llm.enabled(), "ocr_available": ocr.available()}

@app.post("/users")
def create_user(body: schemas.UserIn, db: Session = Depends(get_db), a=Depends(require("admin"))):
    if len(body.password) < 10:
        raise HTTPException(400, "Password minimal 10 karakter")
    if db.query(models.User).filter_by(username=body.username).first():
        raise HTTPException(409, "Username sudah ada")
    db.add(models.User(username=body.username, password_hash=auth.hash_password(body.password), role=body.role))
    log(db, a, "create_user", body.username); db.commit()
    return {"ok": True}

@app.get("/users")
def list_users(db: Session = Depends(get_db), a=Depends(require("admin"))):
    return [{"id": u.id, "username": u.username, "role": u.role, "active": u.active} for u in db.query(models.User).all()]

@app.post("/users/{uid}/active")
def set_active(uid: int, active: bool, db: Session = Depends(get_db), a=Depends(require("admin"))):
    u = db.get(models.User, uid)
    if not u or u.id == a.id:
        raise HTTPException(400, "Tidak dapat mengubah akun ini")
    u.active = active; log(db, a, "set_active", f"{u.username}={active}"); db.commit()
    return {"ok": True}

@app.get("/activity")
def activity(db: Session = Depends(get_db), a=Depends(require("admin"))):
    rows = db.query(models.ActivityLog).order_by(models.ActivityLog.id.desc()).limit(200).all()
    return [{"at": r.at.isoformat(), "user": r.user, "action": r.action, "target": r.target} for r in rows]

# ---------- klasifikasi & aturan
@app.post("/classify")
def classify(body: schemas.ClassifyIn, u=Depends(require(*ANY))):
    return classify_instrument(body.model_dump())

@app.get("/rules")
def rules(instrument: str | None = None, u=Depends(require(*ANY))):
    return {"version": RULES_VERSION, "rules": [r for r in RULES if not instrument or instrument in r["applies_to"]]}

@app.post("/audit")
def audit(body: schemas.AuditIn, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    r = run_audit(body.instrument, body.facts)
    run = models.AuditRun(instrument=body.instrument, facts=body.facts, findings=r["findings"], score=r["score"],
                          status=r["status"], rules_version=r["rules_version"], user_id=u.id)
    db.add(run); log(db, u, "audit", body.instrument); db.commit()
    return {**r, "run_id": run.id}

# ---------- dokumen
@app.post("/documents")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), u=Depends(require(*ANY))):
    data = await file.read()
    try:
        ex = extract_text(file.filename or "", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    inst = guess_instrument(ex["text"])
    doc = models.Document(filename=file.filename, owner_id=u.id, sha256=hashlib.sha256(data).hexdigest(),
                          instrument_guess=inst, needs_ocr=ex["needs_ocr"], ocr_used=ex["ocr_used"], text=ex["text"])
    db.add(doc); db.flush()
    clauses = segment(ex["text"])
    db.add_all([models.Clause(doc_id=doc.id, number=c["number"], text=c["text"]) for c in clauses])
    log(db, u, "upload", f"doc#{doc.id}"); db.commit()
    return {"document_id": doc.id, "instrument_guess": inst, "pages": ex["pages"], "needs_ocr": ex["needs_ocr"],
            "ocr_used": ex["ocr_used"], "ocr_note": ex["ocr_note"], "n_clauses": len(clauses),
            "clauses": [c["number"] for c in clauses], "suggested_facts": suggest_facts(ex["text"], inst),
            "citations": check_citations(ex["text"], db),
            "catatan": "Saran fakta berbasis kata kunci; konfirmasi manual sebelum audit."}

def _doc(db, doc_id, u):
    doc = db.get(models.Document, doc_id)
    if not doc or not can_see(u, doc.owner_id):
        raise HTTPException(404, "Dokumen tidak ditemukan")
    return doc

@app.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    doc = _doc(db, doc_id, u)
    cl = db.query(models.Clause).filter_by(doc_id=doc_id).all()
    return {"id": doc.id, "filename": doc.filename, "instrument_guess": doc.instrument_guess,
            "clauses": [{"number": c.number, "text": c.text} for c in cl]}

@app.post("/documents/{doc_id}/audit")
def audit_document(doc_id: int, body: schemas.DocAuditIn, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    doc = _doc(db, doc_id, u)
    inst = body.instrument or doc.instrument_guess
    if not inst:
        raise HTTPException(400, "Instrumen belum dikenali; isi field instrument.")
    facts = {k: v["value"] for k, v in suggest_facts(doc.text, inst).items() if body.use_suggested}
    facts.update(body.facts)
    r = run_audit(inst, facts)
    r["citations"] = check_citations(doc.text, db)
    run = models.AuditRun(instrument=inst, facts=facts, findings=r["findings"], score=r["score"], status=r["status"],
                          rules_version=r["rules_version"], user_id=u.id, doc_id=doc.id)
    db.add(run); log(db, u, "audit_doc", f"doc#{doc.id}"); db.commit()
    return {**r, "run_id": run.id}

@app.post("/documents/{doc_id}/llm-review")
def llm_review(doc_id: int, body: schemas.LlmReviewIn, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    if not llm.enabled():
        raise HTTPException(503, "Pembacaan AI dinonaktifkan oleh administrator.")
    if not body.confirm_external:
        raise HTTPException(400, "Perlu persetujuan eksplisit: teks dokumen akan dikirim ke layanan AI eksternal.")
    doc = _doc(db, doc_id, u)
    inst = body.instrument or doc.instrument_guess
    if not inst:
        raise HTTPException(400, "Instrumen belum dikenali; isi field instrument.")
    refs = [f"{n.level} {n.nomor}/{n.tahun}" for n in db.query(models.Norma).filter_by(verified=True, status="berlaku").all()]
    try:
        res = llm.review(doc.text, inst, refs)
    except Exception as e:
        raise HTTPException(502, f"Layanan AI gagal: {type(e).__name__}")
    log(db, u, "llm_review", f"doc#{doc.id}"); db.commit()
    return res

# ---------- basis peraturan
@app.post("/norma")
def add_norma(body: schemas.NormaIn, db: Session = Depends(get_db), u=Depends(require("admin", "reviewer"))):
    n = models.Norma(**body.model_dump()); db.add(n); log(db, u, "add_norma", f"{body.level} {body.nomor}/{body.tahun}")
    db.commit(); db.refresh(n)
    return {"id": n.id}

@app.get("/norma")
def list_norma(verified: bool | None = None, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    q = db.query(models.Norma)
    if verified is not None:
        q = q.filter(models.Norma.verified == verified)
    return [{"id": n.id, "level": n.level, "nomor": n.nomor, "tahun": n.tahun, "judul": n.judul,
             "status": n.status, "verified": n.verified} for n in q.all()]

# ---------- review manusia
@app.get("/audit-runs")
def audit_runs(db: Session = Depends(get_db), u=Depends(require(*ANY))):
    q = db.query(models.AuditRun).order_by(models.AuditRun.id.desc())
    if u.role == "penyusun":
        q = q.filter(models.AuditRun.user_id == u.id)
    out = []
    for r in q.limit(100).all():
        rv = db.query(models.Review).filter_by(run_id=r.id).order_by(models.Review.id.desc()).first()
        out.append({"id": r.id, "instrument": r.instrument, "status": r.status, "score": r.score,
                    "created_at": r.created_at.isoformat(), "findings": len(r.findings),
                    "review": {"decision": rv.decision, "by": rv.reviewer, "note": rv.note} if rv else None})
    return out

@app.post("/audit-runs/{run_id}/review")
def review_run(run_id: int, body: schemas.ReviewIn, db: Session = Depends(get_db), u=Depends(require("admin", "reviewer"))):
    if not db.get(models.AuditRun, run_id):
        raise HTTPException(404, "Hasil audit tidak ditemukan")
    db.add(models.Review(run_id=run_id, reviewer=u.username, decision=body.decision, note=body.note))
    log(db, u, "review", f"run#{run_id}:{body.decision}"); db.commit()
    return {"ok": True}

# ---------- draf
@app.get("/draft/fields")
def draft_fields(instrument: str, u=Depends(require(*ANY))):
    if instrument not in tpl.FIELDS:
        raise HTTPException(404, "Instrumen tidak dikenal")
    return [{"key": k, "label": l, "multiline": bool(m)} for k, l, m in tpl.FIELDS[instrument]]

@app.post("/draft/preview")
def draft_preview(body: schemas.DraftIn, u=Depends(require(*ANY))):
    return tpl.build(body.instrument, body.inputs)

@app.post("/draft/docx")
def draft_docx(body: schemas.DraftIn, db: Session = Depends(get_db), u=Depends(require(*ANY))):
    res = tpl.build(body.instrument, body.inputs)
    log(db, u, "draft_docx", body.instrument); db.commit()
    return Response(tpl.to_docx(res), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="draf-{body.instrument}.docx"'})

STATIC = pathlib.Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
