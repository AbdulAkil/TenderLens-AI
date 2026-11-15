# Deployment preparation — no deployment performed

For a small pilot, a single EU-region Linux VPS with Docker Compose is the simplest
architecture: HTTPS reverse proxy → Next.js → private FastAPI → private PostgreSQL;
the dedicated worker uses the same database. Start with adequate RAM for Next.js builds
and PostgreSQL, encrypted off-host backups, firewall and operator monitoring.

A managed frontend/backend/database split reduces host maintenance but requires a
separate always-on worker, connection/TLS configuration, explicit cookies/origins,
pgvector availability and several billing/region boundaries. It generally costs more
at low volume. The repository does not provision either option.

## Before starting any externally reachable service

1. Obtain explicit deployment approval and choose an EU host/domain.
2. Install patched Docker/Compose, firewall all except required SSH and HTTPS.
3. Create `.env` from the example with strong unique DB credentials. URL-encode any
   password in DATABASE_URL. Set `ENVIRONMENT=production`, HTTPS `SITE_URL`, matching
   `NEXT_PUBLIC_SITE_URL` and exact HTTPS `CORS_ALLOWED_ORIGINS`. Remove local origins.
4. Keep `.env` private (0600 on Linux), out of Git and backups unless encrypted.
5. Keep AI disabled, email dry-run/review, and Stripe test-only until separately reviewed.
6. Recheck source permissions, terms/privacy, GDPR processing records and seller identity.

```sh
docker compose config --quiet
docker compose build
docker compose up -d
docker compose exec api alembic current
curl --fail http://127.0.0.1:8000/ready
curl --fail http://127.0.0.1:3000/
```

Configure a host HTTPS reverse proxy to `127.0.0.1:3000` (for example Caddy with your
actual approved domain). Do not expose DB/API/admin ports separately. Set body/time
limits and deploy an external uptime check. The frontend API proxy preserves cookies;
requests must carry the external trusted Origin. Validate this on the final domain.

Keep the DB volume persistent. Apply migrations once, before exposing a release.
The API currently runs Alembic on startup, appropriate for one API process; use an
explicit migration release step before scaling. Images run without root. Pin tested
base-image digests in your release process and use lockfiles for dependency builds.

## Rollback

Tag/retain the previous application images and a verified pre-migration backup. Stop
the worker before maintenance. Compatible application rollbacks can reuse additive
schemas. The commercial tenant migration is deliberately forward-only; do not drop
tenant tables to roll back. Restore the backup into a new database, verify it, and
switch configuration during an approved maintenance window. Never delete the volume
as a routine rollback command.

## Release acceptance

Run the complete workflow on PostgreSQL, replay signed provider test webhooks, verify
actual sandbox email receipt, test expired subscriptions and cross-tenant access, then
rehearse restore. Local SQLite/browser tests and offline migration SQL cannot establish
those production guarantees. See [launch checklist](launch-checklist.md).
