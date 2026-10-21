# Legal Audit & Drafting - Dinas Kesehatan (kerangka backend)

Jalankan: `docker compose up` lalu buka http://localhost:8000/docs

Endpoint: `POST /classify` (pilih instrumen), `POST /audit` (jalankan rule), `GET /rules`, `POST|GET /norma` (basis peraturan).

Contoh audit Keputusan Bupati:
curl -X POST localhost:8000/audit -H 'content-type: application/json' \
 -d '{"instrument":"kepbup","facts":{"memuat_norma_umum":true,"ada_dasar_kewenangan":false}}'

Struktur: app/rules/rules.yaml (rule + dasar hukum, edit tanpa ubah kode), app/audit/engine.py (evaluasi + skor),
app/audit/classify.py (decision tree), app/models.py (norma, jejak audit), docker-compose.yml (PostgreSQL + pgvector).

Penting: butir bertanda [VERIFIKASI] di rules.yaml harus dicek ke JDIH/peraturan.bpk.go.id sebelum dipakai.
Hasil adalah alat bantu telaah dan wajib direview Bagian Hukum. Ganti password database sebelum dipakai.

Tahap berikut: login/RBAC, unggah dokumen + parsing pasal, RAG peraturan (pgvector), generator draf dan memo, frontend.

## Unggah dokumen (PDF/DOCX)
`POST /documents` (multipart, field `file`) -> ekstraksi teks, segmentasi Pasal/BAB/diktum, tebakan jenis instrumen,
saran fakta dengan kutipan bukti, dan cek dasar hukum terhadap tabel `norma`.
`POST /documents/{id}/audit` -> jalankan rule; `facts` yang Anda isi menimpa saran otomatis.
Contoh: curl -F file=@draf.docx localhost:8000/documents
Antarmuka web: buka http://localhost:8000/ . Draf: POST /draft/preview dan /draft/docx.
Catatan: PDF hasil scan ditandai `needs_ocr` (OCR belum ada). File asli tidak disimpan, hanya teks. Format .doc lama: simpan ulang sebagai .docx.

## Keamanan, peran, OCR, dan AI
1. `cp .env.example .env`, isi SECRET_KEY, ADMIN_PASSWORD, POSTGRES_PASSWORD, lalu `docker compose up --build`.
   Bila sebelumnya sudah menjalankan versi lama: `docker compose down -v` (skema database berubah).
2. Peran: **penyusun** (unggah, audit, draf; hanya melihat dokumennya sendiri), **reviewer** (melihat semua, memberi keputusan
   disetujui/revisi/ditolak, mengelola basis peraturan), **admin** (semua + kelola pengguna + log aktivitas).
3. OCR: image Docker memasang tesseract (ind+eng). Hasil OCR ditandai dan wajib diperiksa manual.
4. Pembacaan klausul AI: `LLM_ENABLED=0` bawaan. Bila `1`, teks dokumen DIKIRIM ke layanan eksternal (Anthropic API) setelah
   pengguna mencentang persetujuan. Pastikan sesuai kebijakan data instansi. Keluaran divalidasi: kutipan harus ada di dokumen,
   rujukan hukum dicek ke tabel `norma` terverifikasi; saran tidak masuk skor otomatis.
5. Akses hanya ke 127.0.0.1:8000. Untuk akses jaringan pasang reverse proxy dengan HTTPS.
6. Uji: `python3 tests/test_core.py`
