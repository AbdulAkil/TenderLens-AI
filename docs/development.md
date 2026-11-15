# Development

Use Python 3.12+, Node 22+, PostgreSQL 16 with pgvector. Existing source remains in
`backend/src/tenderlens` and `frontend`. No paid services are required.

## Docker

```sh
cp .env.example .env
docker compose up --build
```

Open http://localhost:3000. API binds loopback at port 8000. PostgreSQL has no host
port. The API migrates before serving; the worker waits for readiness. Keep exactly
one worker for the supported pilot deployment. Docker daemon must be running.

## Native setup (PowerShell)

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -e './backend[dev]'
cd frontend
npm ci
npm run dev
```

In a second terminal, set `DATABASE_URL` to your local PostgreSQL connection, run
`alembic upgrade head` from backend, and start `uvicorn tenderlens.main:app`.
Run `python -m tenderlens.saas.worker` separately. Native Next.js proxies to
127.0.0.1:8000; Docker builds bake in `API_INTERNAL_URL=http://api:8000`.
Set `PYTHONUTF8=1` on Windows for Unicode source data and CLI output.

## First account in dry run

1. Open `/auth/signup`, accept the pilot terms and create an account.
2. Run `docker compose exec api python -m tenderlens.saas.cli outbox`.
3. Find the verification delivery ID, then run
   `docker compose exec api python -m tenderlens.saas.cli preview --id <UUID>`.
4. Open the link locally, click Verify email, sign in and complete `/onboarding`.
5. Set `ADMIN_EMAILS` to your verified operator email and restart API/worker to
   grant internal admin access. Never grant access based on a frontend flag.
6. Set notification preferences. Visit `/dashboard`, refresh matches and save a
   real notice. Review digests at `/admin`; dry run records delivery without sending.

Do not reuse the browser test server for deployment. `scripts/pilot_test_server.py`
is an ephemeral SQLite fixture harness with test-only token access and binds loopback.
The Docker API image does not copy that script.

## Configuration

`.env.example` is the configuration catalog. Important groups:

- `ENVIRONMENT`, `SITE_URL`, explicit `CORS_ALLOWED_ORIGINS`, `SESSION_HOURS`.
- `TRIAL_DAYS`, `PLANS_JSON`, Stripe test price IDs and test webhook secret.
- `EMAIL_PROVIDER=dry_run|resend`, sandbox allowlist, approval and webhook secret.
- `TED_INGESTION_ENABLED`, expert `INGESTION_QUERY`, bounded notice count.
- Existing document/embedding/LLM flags. Customer AI additionally requires a positive
  per-organization monthly budget. Default budget is zero.

Blank provider keys stay blank. Do not copy production credentials into this repo.
`PLANS_JSON` is optional; an empty value uses the defaults. All prices are hypotheses.
