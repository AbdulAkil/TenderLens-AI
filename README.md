# TenderLens AI

Procurement intelligence for Belgian SMEs: official notices, company-specific matching,
evidence-led screening, saved opportunities and scheduled tender digests.

**Status: commercial pilot implementation; external activation and review still required.**
No live payments, real-recipient email, paid AI calls or public deployment were activated.
See the [completion matrix and verification report](docs/readiness-report.md).

## Start locally

```sh
cp .env.example .env
docker compose up --build
```

Open http://localhost:3000. PostgreSQL stays private; API port 8000 binds loopback.
The API applies migrations; the independent worker schedules background jobs. Email
defaults to a database dry run with digest review. AI defaults off and zero budget.
The app remains useful without paid services. Production configuration rejects sample
credentials and insecure origins; local defaults are for development only.

Create an account at `/auth/signup`, inspect the dry-run verification delivery through
the operator CLI, verify, sign in and complete onboarding:

```sh
docker compose exec api python -m tenderlens.saas.cli outbox
docker compose exec api python -m tenderlens.saas.cli preview --id <delivery-UUID>
```

Ingest official notices deliberately or enable scheduled TED ingestion:

```sh
docker compose exec api python -m tenderlens.ingestion.cli --query 'buyer-country = BEL' --scope ACTIVE --max-notices 100
docker compose exec api python -m tenderlens.saas.worker --once
```

`--all-versions` supports historical/superseded publication backfills. Regular ingestion
uses latest versions and a rolling window; full national coverage is not claimed.

## Implemented

- Verified email accounts, Argon2 passwords, expiring/revocable sessions and resets.
- Organizations, roles, tenant-scoped profiles/saved tenders/matches/feedback.
- TED normalization, unchanged detection, source revisions and reviewed manual imports.
- Deterministic multilingual keyword matching, explicit unknowns, evidence extraction.
- Durable scheduled jobs, retries/recovery, daily/weekly digests, reminders, review/outbox.
- Configurable plans/quotas, Stripe test Checkout/portal and signed/idempotent webhooks.
- Marketing, pricing, auth/onboarding, opportunities, discovery, details, comparison,
  saved tenders, profiles, notifications, billing, team/settings and internal admin.
- Privacy export, deletion requests, retention tasks, audit events and pilot inquiries.
- Backend tests on SQLite/PostgreSQL, production build, browser workflow and CI.

## Stack

Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16/pgvector, Next.js 15.5.29,
React 19, TypeScript, dedicated Python worker, Docker Compose. No Redis required.
Optional model providers remain behind evidence checks and cost reservations.

## Documentation

| Guide | Purpose |
|---|---|
| [Development](docs/development.md) | Setup, accounts, environment and commands |
| [Architecture](docs/architecture.md) | Boundaries, tenant model and data flow |
| [Data sources](docs/data-sources.md) | Verified TED contract and Belgian coverage limits |
| [Matching](docs/matching.md) | Formula, uncertainty, feedback and evaluation limits |
| [Email](docs/email.md) | Review, dry run, sandbox setup, retries and webhooks |
| [Billing](docs/billing.md) | Plans, Stripe test lifecycle and VAT/invoicing boundaries |
| [Security](docs/security.md) | Access controls and required security review |
| [Privacy operations](docs/privacy-operations.md) | Processing/retention inventory for legal review |
| [Testing](docs/testing.md) | Commands, actual coverage and validation boundaries |
| [Deployment](docs/deployment.md) | Host configuration, release and rollback |
| [Operations](docs/operations.md) | Worker, monitoring, backups and restore |
| [Launch checklist](docs/launch-checklist.md) | Required external activation gates |
| [Commercial playbook](docs/commercial-playbook.md) | Pilot interviews and first-customer assets |
| [Readiness report](docs/readiness-report.md) | Completion matrix, costs and known limitations |

Prices are hypotheses. No eligibility, coverage, legal compliance or match-quality
guarantee is made. National feed integration, full translation, reviewed matching
evaluation, real provider sandbox tests and legal/accounting approval remain open.

MIT. See [LICENSE](LICENSE).
