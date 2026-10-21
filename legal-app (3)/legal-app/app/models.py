from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Norma(Base):
    """Basis pengetahuan peraturan. `verified` = sudah dicek manual ke sumber resmi."""
    __tablename__ = "norma"
    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(20))      # UU, PP, Perpres, Permen, Perda, Perbup
    nomor: Mapped[str] = mapped_column(String(20))
    tahun: Mapped[int] = mapped_column(Integer)
    judul: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="berlaku")  # berlaku/diubah/dicabut
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

class AuditRun(Base):
    """Jejak audit: input, temuan, versi aturan."""
    __tablename__ = "audit_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    instrument: Mapped[str] = mapped_column(String(10))
    facts: Mapped[dict] = mapped_column(JSON)
    findings: Mapped[list] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40))
    rules_version: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

class Document(Base):
    """Hanya teks hasil ekstraksi yang disimpan; file asli tidak disimpan (minimisasi data)."""
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    filename: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False)
    sha256: Mapped[str] = mapped_column(String(64))
    instrument_guess: Mapped[str | None] = mapped_column(String(10), nullable=True)
    needs_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(Text)

class Clause(Base):
    __tablename__ = "clause"
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(Integer, index=True)
    number: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(Text)

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20))      # admin | reviewer | penyusun
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Review(Base):
    __tablename__ = "review"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, index=True)
    reviewer: Mapped[str] = mapped_column(String(60))
    decision: Mapped[str] = mapped_column(String(20))  # disetujui | revisi | ditolak
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(120), default="")
