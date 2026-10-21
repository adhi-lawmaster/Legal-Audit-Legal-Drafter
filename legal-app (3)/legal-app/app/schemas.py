from typing import Literal
from pydantic import BaseModel

Instrument = Literal["perda", "perbup", "kepbup", "mou", "pks"]

class ClassifyIn(BaseModel):
    mengatur_norma_umum: bool = False
    membebani_hak_kewajiban_sanksi_pungutan: bool = False
    menjabarkan_peraturan_di_atasnya: bool = False
    kerja_sama: bool = False
    hak_kewajiban_mengikat: bool = False

class AuditIn(BaseModel):
    instrument: Instrument
    facts: dict[str, bool | None]   # jawaban checklist; None = belum dijawab

class NormaIn(BaseModel):
    level: str
    nomor: str
    tahun: int
    judul: str
    status: str = "berlaku"
    verified: bool = False
    source_url: str | None = None

class DocAuditIn(BaseModel):
    instrument: Instrument | None = None
    facts: dict[str, bool | None] = {}
    use_suggested: bool = True

class DraftIn(BaseModel):
    instrument: Instrument
    inputs: dict[str, str] = {}

class LoginIn(BaseModel):
    username: str
    password: str

class UserIn(BaseModel):
    username: str
    password: str
    role: Literal["admin", "reviewer", "penyusun"]

class ReviewIn(BaseModel):
    decision: Literal["disetujui", "revisi", "ditolak"]
    note: str = ""

class LlmReviewIn(BaseModel):
    instrument: Instrument | None = None
    confirm_external: bool = False   # persetujuan eksplisit: teks dikirim ke layanan AI eksternal
