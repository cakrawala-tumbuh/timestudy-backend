# TimeStudy — Backend API

REST API for the TimeStudy system. Manages respondents, daily work-time logs, and provides an **OAuth2 PKCE** authorization server for the Android client app.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI 0.115 |
| Database | SQLite (via SQLAlchemy 2.0) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| OAuth2 | Custom PKCE server (RFC 6749 + RFC 7636) |
| API Docs | Swagger UI / ReDoc (built-in FastAPI) |
| Tests | pytest + pytest-cov |

---

## Quick Start

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd timestudy-backend

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — at minimum, set a strong SECRET_KEY

# 5. Run migrations and seed initial data
alembic upgrade head
python scripts/seed.py

# 6. Start the development server
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## Running Tests

```bash
pytest
# With coverage report:
pytest --cov=app --cov-report=html
```

---

## Generating API Documentation

### Swagger UI / ReDoc (runtime)

Available automatically when the server is running:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`
- **OpenAPI JSON** — `http://localhost:8000/openapi.json`

### pdoc (static Python docs)

```bash
# Install dev dependencies first
pip install -e ".[dev]"

# Generate HTML docs → docs/
pdoc app -o docs

# Serve locally (auto-reload on change)
pdoc app
```

Output is written to `docs/` and can be hosted as a static site.

---

## OAuth2 PKCE Flow (Android App)

The Android app uses [AppAuth](https://github.com/openid/AppAuth-Android) with PKCE.

1. **Register a client** via the admin portal or API:
   ```
   POST /api/v1/oauth/clients
   ```

2. **Authorization request** (GET):
   ```
   GET /oauth/authorize
     ?response_type=code
     &client_id=<client_id>
     &redirect_uri=com.example.timestudy://callback
     &scope=sync
     &code_challenge=<S256 challenge>
     &code_challenge_method=S256
   ```
   The user logs in with their `resp_id` and PIN on the shown page.

3. **Token exchange** (POST form):
   ```
   POST /oauth/token
   grant_type=authorization_code
   &client_id=<client_id>
   &code=<code>
   &redirect_uri=com.example.timestudy://callback
   &code_verifier=<verifier>
   ```

4. **Refresh token**:
   ```
   POST /oauth/token
   grant_type=refresh_token
   &client_id=<client_id>
   &refresh_token=<refresh_token>
   ```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | JWT signing key — use `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | `sqlite:///./timestudy.db` | SQLAlchemy connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Admin JWT lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Admin refresh token lifetime |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowed origins |
| `FIRST_ADMIN_USERNAME` | `admin` | Username for seeded superadmin |
| `FIRST_ADMIN_PASSWORD` | `changeme123` | Password for seeded superadmin |

See `.env.example` for the full list.

---

## Docker

```bash
# Build
docker build -t timestudy-backend .

# Run
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -v $(pwd)/data:/data \
  timestudy-backend
```

---

## Project Structure

```
app/
├── main.py          — FastAPI application factory
├── config.py        — Settings (pydantic-settings)
├── database.py      — SQLAlchemy engine and session
├── dependencies.py  — FastAPI dependencies (auth guards)
├── models/          — SQLAlchemy ORM models
├── schemas/         — Pydantic request/response schemas
├── routers/         — FastAPI route handlers
└── services/        — Business logic (auth, OAuth2)
alembic/             — Database migrations
scripts/             — Utility scripts (seed, etc.)
tests/               — pytest test suite
```

---

## CI / CD

| Trigger | Jobs |
|---------|------|
| Every push / PR | `lint` → `test` |
| Push tag `v*` | `test` → `build-docker` (GHCR) + `build-pip` + `publish-pypi` |

---

## License

MIT
