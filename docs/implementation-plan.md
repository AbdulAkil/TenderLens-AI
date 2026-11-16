# Commercial implementation checklist

## Baseline — 2026-11-15

Starting commit: c7d1869. Clean working tree. Two commits; no AGENTS.md found.
Reuse FastAPI/SQLAlchemy/PostgreSQL, six Alembic migrations, TED v3 transport,
normalization, document processing, lexical/vector retrieval, rules analysis,
matching, saved opportunities and the Next.js application. No rewrite.

Security findings: unauthenticated private company routes; global company names;
unbounded matching; no session, membership, billing or worker; unbounded document
downloads with redirects; deadline normalization discards time; unknown eligibility
earns positive scoring; frontend stores company selection without authorization.

Baseline attempted before source edits: Python 3.12 lacks pytest; Python 3.13
pytest cannot collect (missing FastAPI/SQLAlchemy). Installing isolated dependencies.
Docker CLI exists but daemon is unavailable. Frontend dependencies initially absent;
default npm cache is inaccessible, retrying with workspace cache. These are baseline
environment failures, not passing checks.

## Ordered work and acceptance criteria

- [x] Audit and isolated feature branch `feat/commercial-pilot`.
- [x] Secure foundation: opaque, hashed server-side sessions; Argon2 passwords;
  verification/reset tokens; organizations/memberships; scoped company repository;
  cross-tenant API tests; migration preserves orphaned legacy profiles privately.
- [ ] Intelligence: unchanged notice detection, revision history, accurate timestamps,
  hard exclusions/expired deadlines, multilingual terms, unknown eligibility,
  bounded incremental matching and feedback.
- [ ] Customer workflow: signup → verification → profile → matches → approved digest
  → sandbox delivery → saved tender → preferences, with persisted idempotency.
- [x] Frontend: public site, auth/onboarding, dashboard, discovery, detail, saved,
  profile, notifications, comparison, billing, settings and protected admin.
- [ ] Billing: configurable plans/quotas; Stripe test-only checkout/portal;
  signed, idempotent webhooks; tenant subscription checks and lifecycle tests.
- [x] Reliability: PostgreSQL job claims/leases/retries, digest outbox, admin review,
  health, retention, exports/deletion requests and audit events.
- [x] Production preparation: CI, build, migration tests, dependency audits,
  hardened Compose, backup/restore instructions and external activation gates.
- [x] Launch assets: evidence-honest example report, pilot leads, founder materials,
  sourced legal/data-source notes, cost scenarios, final completion matrix.

Every claimed completion must have recorded verification. No deployment, paid API
calls, live checkout, real-recipient messages or infrastructure provisioning.

## Decisions

Initial validation segment: Belgian IT/software and cybersecurity SMEs. Industry
remains configurable. Retain one default organization per account, owner/admin/member
roles; Business permits additional profiles and members. PostgreSQL-backed worker
avoids new queue infrastructure. Opaque cookies use HttpOnly, SameSite=Lax, expiry,
server-side revocation and strict Origin validation. Email defaults to a database
outbox dry run with administrator review. Trials and prices are configuration.

## Completion evidence and remaining acceptance

- Foundation milestone committed as 7142c02; additional verification and fixes follow.
- Original baseline 19 passing; final suite runs on SQLite and disposable PostgreSQL16.
- Customer browser workflow, production build, locked Docker images, local Compose
  readiness and all enabled worker jobs have been exercised.
- Official historical TED notice imported/replayed unchanged; official XML processed
  into 17 chunks; real PostgreSQL lexical retrieval and one-case evaluation verified.
- Intelligence remains partial for national coverage, cross-publication versions,
  comprehensive eligibility and reviewed Belgian matching performance.
- Customer workflow is verified in dry run; external sandbox email receipt requires
  credentials and separately authorized recipient delivery.
- Billing has SDK/mocked lifecycle coverage; real Stripe test checkout and tax/invoice
  integration require external setup.
- See docs/readiness-report.md for the authoritative feature matrix, commands, costs,
  activation checklist and unimplemented items. No production launch claim.
