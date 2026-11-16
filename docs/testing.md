# Verification

## Commands

```sh
cd backend
python -m pytest -q
ruff check .
ruff format --check .
alembic upgrade head --sql
alembic heads
python -m pip_audit
cd ../frontend
npm ci
npm run lint
npm run typecheck
npm run build
npm audit
npx playwright install chromium
npm run test:e2e
```

On Windows use the `.venv/Scripts` executables and set `PYTHONUTF8=1`.
If browser-cache permissions require it, set `PLAYWRIGHT_BROWSERS_PATH` to
`<workspace>/.cache/browsers` both for installation and tests.

The original baseline at c7d1869 passed 19 tests after isolated dependencies were
installed. Backend commercial tests use actual ORM persistence on ephemeral SQLite
with JSONB/TSVECTOR compilation substitutes. They test API auth/verification/reset,
tenant isolation, entitlements, digest selection/deduplication, preferences, HTML/URL
safety, shared rate limits, unchanged notice revisions, timezone parsing, SSRF,
prompt-injected facts and signed Stripe webhook replay. The suite was also executed using disposable PostgreSQL schemas via
`TEST_DATABASE_URL`. SQLite alone does not verify
PostgreSQL full-text/vector search, advisory locks, row-lock concurrency or migrations.

Browser tests run a production Next.js build against the actual loopback FastAPI
fixture harness, with no frontend API mocks. They cover public pages, signup,
verification, login, onboarding, matching, saved tenders, notifications, billing
configuration errors, mobile overflow and logout. Test-only emails and tender records
are visibly marked fixtures. Token inspection exists only in the external test script.

Stripe tests use the SDK signature verifier and mocked provider current state; they
are not live test Checkout payments. Email tests use dry run; inbox/provider rendering
is not verified. A real TED search returned HTTP 200 with the current projection.
No live paid API requests or real-recipient sends were performed.

CI provisions PostgreSQL 16/pgvector, applies all migrations twice, checks schema,
runs backend tests, frontend lint/type/build/audit and the browser workflow. Those
hosted CI jobs must actually run before treating their configuration as passing.
The daemon was started for isolated validation: images built, migrations ran on
PostgreSQL16, and the local Compose API/proxy/worker checks succeeded.

See `docs/readiness-report.md` for the final measured results and outstanding gates.
Do not reinterpret missing external credentials as completed provider verification.
