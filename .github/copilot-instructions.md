# Copilot Instructions — Time Study Backend YPII

## Stack

| Komponen | Detail |
|---|---|
| Framework | FastAPI |
| Auth | OAuth2 (JWT access + refresh token) |
| Database | SQLAlchemy + Alembic migrations |
| Runtime | Python 3.11 |
| Deployment | Docker (GHCR) |

---

## Arsitektur

```
app/
  routers/      → FastAPI route handlers (thin layer, no business logic)
  services/     → Business logic, orchestration
  models/       → SQLAlchemy ORM models
  schemas/      → Pydantic request/response schemas
  dependencies/ → FastAPI dependency injection
  config.py     → Settings via pydantic-settings
  database.py   → SQLAlchemy engine, session factory
```

---

## Environment Variables

| Variabel | Catatan |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg2://...` atau `sqlite:///...` |
| `SECRET_KEY` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |

---

## Konvensi Kode

- Router hanya boleh memanggil service, tidak boleh langsung akses database.
- Semua validasi input via Pydantic schema.
- Gunakan dependency injection (`Depends`) untuk session DB dan auth.
- Alembic digunakan untuk semua perubahan skema — jangan ubah skema secara manual.

---

## Testing

- Framework: pytest
- Jalankan: `pytest --cov=app --cov-report=xml`
- Gunakan `requirements-dev.txt` untuk dependensi dev/test.

---

## CI/CD

### Trigger GitHub Actions

| Event | Job |
|---|---|
| PR ke `master` | `lint`, `unit test` |
| Push tag `v*` | `publish` (build + push Docker image ke GHCR) |
| `workflow_dispatch` | Semua job CI |

- PR **tidak boleh** di-merge jika ada job CI yang gagal.
- Push langsung ke `master` **tidak** mentrigger CI — semua harus via PR.

---

## Workflow Git & Versioning

### Commit
- Saat diminta commit, lakukan langsung.
- Format commit message: `<type>(<scope>): <deskripsi singkat>`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `build`
  - Scope opsional: nama router, service, model, atau file utama yang berubah
  - Tambahkan body untuk menjelaskan **apa** yang berubah dan **mengapa** jika tidak sudah jelas
- Contoh: `feat(auth): tambah endpoint refresh token`

### Push
- Saat diminta push, push ke branch fitur aktif — **bukan** `master`.
- `master` hanya bisa diubah via Pull Request yang sudah lulus semua CI test.
- Contoh: `git push origin feature/nama-fitur`

### Branch Strategy
- `master`: protected — semua perubahan via PR.
- Nama branch: `feature/<nama>`, `fix/<nama>`, `chore/<nama>`, `docs/<nama>`

### Versioning & Tagging
Format: `vMAJOR.MINOR.PATCH` (Semantic Versioning)

| Jenis Perubahan | Bump | Contoh |
|---|---|---|
| Bug fix, hotfix, perbaikan kecil, docs | PATCH | `v1.0.0` → `v1.0.1` |
| Fitur baru, endpoint baru, perubahan non-breaking | MINOR | `v1.0.0` → `v1.1.0` |
| Breaking change API, perombakan skema DB, perubahan auth | MAJOR | `v1.0.0` → `v2.0.0` |

- Saat diminta membuat tag, tentukan bump berdasarkan tabel di atas, lalu:
  ```
  git tag -a vX.Y.Z -m "<ringkasan perubahan>"
  git push origin vX.Y.Z
  ```
- Tag dibuat di commit `master` terbaru (setelah PR di-merge).
