# TenderLens commercial implementation report — 2026-11-15

## A. Product summary

The repository now contains a working commercial pilot workflow: create and verify an
account, sign in, configure a company, ingest official notices, calculate inspectable
matches, save opportunities, give feedback, configure digests, review them internally
and execute dry-run delivery. A public website and customer/admin workspace connect to
real backend APIs. No invented tenders populate the production database.

This is **not a declaration of production launch readiness**. Real provider sandbox
activation, legal/accounting work and the remaining product limitations below must be
resolved before external commercial release. No public deployment, live payment,
paid LLM call or real-recipient email was performed.

## B. Architecture

The existing FastAPI/SQLAlchemy/PostgreSQL/pgvector procurement engine is retained.
Two additive migrations introduce identity/tenant/commercial records and explicit
notice status. Next.js 15.5.29 uses a same-origin API proxy. A dedicated Python worker
uses PostgreSQL jobs and a transactional email outbox. Stripe and Resend have isolated
test/sandbox adapters. Optional AI uses per-organization cost reservations and strict
evidence fallback. See [architecture](architecture.md) for the actual boundaries.

## C. Feature completion matrix

“Complete” means implemented and locally verified within the described pilot scope,
not independently certified or externally activated.

| Feature | Status | Evidence / boundary |
|---|---|---|
| Signup, verification, login/logout, password reset | Complete | Backend and browser tests; dry-run verification |
| Expiring/revocable secure sessions | Complete | Hash/cookie/reset tests; production Secure setting |
| Organizations, memberships, roles and switching | Complete | Server checks; tenant isolation suite |
| Tenant-scoped profiles, saved opportunities and feedback | Complete | Cross-UUID access denied; quota tests |
| Owner deletion request and privacy export | Partially complete | Request revokes access; final erasure is an operator workflow |
| TED ingestion, retries, pagination, deduplication | Complete | Live bounded import + unchanged replay, mocked transport tests |
| Real notice document processing and lexical retrieval | Complete | Official XML processed: 17 chunks; PostgreSQL returned 3 lexical hits |
| Version/change/cancellation handling | Partially complete | Same-ID revisions and saved changes; explicit imported cancellation; cross-publication TED chains incomplete |
| Belgian national source automation | Blocked | Permitted API contract not verified; no challenge bypass |
| Reviewed manual official-source import | Complete | Validated admin API, actor/provenance recorded; no remote fetch |
| Deterministic matching and unknowns | Partially complete | Bounded scoring/filtering, EN/NL/FR aliases; eligibility assessment and regional/multilingual breadth limited |
| Reviewed matching benchmark | Not implemented | Metrics functions exist; only one reviewed retrieval case, no Belgian matching accuracy claims |
| Structured evidence/rules and optional AI | Partially complete | Grounding/SSRF/prompt tests; provider calls unverified; advanced extraction incomplete |
| AI token/cost tracking and budget boundary | Partially complete | Reservation adapter and returned usage estimates; no actual paid provider invoice validation |
| Daily/weekly digests and saved deadline reminders | Complete | Persisted selection, review, idempotency, preference/dry-run tests |
| Email queue/retry/provider/webhook suppression | Partially complete | Signed Svix tests; real inbox receipt and email-client rendering unverified |
| All requested lifecycle/high-score email categories | Partially complete | Verify/reset/welcome/digest/deadline/update/cancellation; remaining lifecycle automation not finished |
| Public website, pricing, FAQ/support/legal drafts | Complete | Browser route checks; factual historical report source verified |
| Onboarding/dashboard/discovery/detail/saved/profile | Complete | Full browser workflow; real backend, responsive overflow corrected |
| Comparison, notifications, billing and account/team UI | Complete | Connected endpoints; entitlements enforced; not all interactions have browser coverage |
| Dutch/French localization | Partially complete | Central navigation dictionary; page bodies remain English |
| Website-to-profile AI suggestions | Not implemented | Website may be stored; no unsafe arbitrary URL crawler added |
| Configurable plans, trials and quotas | Complete | Server plan checks and tests; prices remain hypotheses |
| Stripe test Checkout/portal/lifecycle | Partially complete | SDK integration + signature/replay/ownership/Checkout mocks; real test account exercise pending |
| Live billing, tax and Peppol invoicing | Blocked | Live keys/events rejected; requires founder/accountant activation and integration |
| Internal administration | Partially complete | Organizations/jobs/review/retry/delivery/usage/pilot leads; advanced support/flags/analytics incomplete |
| Scheduling/retries/recovery/retention | Complete | PostgreSQL-backed jobs; recovery tests; six real Compose jobs completed |
| Cost/resource/product metrics | Partially complete | Audit events, feedback, job results, usage records; no full MRR/churn/gross-margin analytics |
| Docker/CI/release documentation | Complete | Both images built; isolated stack/API/proxy/worker verified; hosted CI not yet run |
| Backup/restore, external alerts and independent security review | Partially complete | Procedures provided; off-host system/restore rehearsal not executed |
| Legal/GDPR/seller identity | Blocked | Technical controls and drafts; counsel/business details/DPAs outstanding |
| Launch/interview/outreach assets | Complete | Repository playbook and opt-in pilot form; nothing sent automatically |

## D. Actual verification

Executed locally:

- Original c7d1869 backend: **19 passed** after dependency setup.
- `python -m pytest -q`: **47 passed** on ephemeral SQLite.
- `TEST_DATABASE_URL=<isolated PostgreSQL16>; python -m pytest backend/tests -q`:
  **47 passed** using isolated per-test schemas with pgvector available.
- `ruff check backend scripts` and `ruff format --check backend`: clean after fixes.
- `npm run lint`, `npm run typecheck`, `npm run build`: successful.
- `npm audit`: zero known vulnerabilities after dependency updates/overrides.
- `python -m pip_audit`: zero known vulnerabilities; local application package cannot
  be audited against PyPI, so application security relies on code review/tests.
- `npm run test:e2e`: **2 passed**, including verified signup through logout and
  mobile overflow checks, against the real loopback fixture API.
- `alembic upgrade head`: all eight migrations applied to disposable PostgreSQL16;
  schema acceptance verified organization/profile/status/vector tables.
- `docker compose config --quiet`, API/frontend image builds: successful.
- Isolated Compose stack: database/API healthy, frontend proxy HTTP200; match,
  analyze(disabled), digest, reminders, changes and cleanup jobs reached `done`.
- Official TED live backfill: publication 556965-2026 inserted once; identical replay
  returned `inserted=0, updated=0, unchanged=1`. Latest-only mode excluded the
  superseded publication, so historical validation explicitly used `--all-versions`.
- Official XML processing completed with 17 chunks; PostgreSQL lexical retrieval
  returned three hits. Existing one-case retrieval smoke report measured Recall@1,
  Recall@5 and MRR 1.0. This is **one historical retrieval case**, not match quality.

Failures encountered and fixed included missing local dependencies, dependency
advisories, Stripe SDK object conversion, wizard premature submission, mobile overflow,
test schema fallback into public, list-valued TED deadlines and SQLite timezone equality.
Sandbox socket interference required approved local execution for PostgreSQL/browser
checks. One upstream Starlette/httpx TestClient deprecation warning remains.

No provider inbox, real Stripe test payment, complete historical corpus, sustained load,
independent penetration test, backup restore or hosted CI run is claimed.

## E. Monthly cost scenarios

Planning allowances in EUR, excluding VAT, payment fees, accounting/Peppol service,
founder labor, support, acquisition and optional AI. These are assumptions, not provider
quotes or measured production costs. One EU VPS, private PostgreSQL, one worker,
one recipient per customer, approximately 30 digest emails/customer/month, limited document processing and shared
corpus. Reserve separate headroom for team recipients and essential emails.

| Customers | VPS / storage | Backup / monitoring | Email allowance | Core monthly total |
|---:|---:|---:|---:|---:|
| 10 | €10–20 | €5–10 | €0–5 | **€15–35** |
| 50 | €20–35 | €5–15 | €0–25 | **€25–75** |
| 100 | €30–50 | €10–20 | €25–30 | **€65–100** |
| 500 | €60–120 | €20–40 | €25–50 | **€105–210** |

AI defaults €0. A configured €1/customer monthly budget would add at most the chosen
budget envelope only if provider price estimates/reservations remain accurate; test
that boundary before use. Scale is not load-tested at 500 customers. Matching/candidate
batch bounds must be revisited before that volume.

Vendor references checked for planning: [Hetzner cloud](https://www.hetzner.com/cloud/)
and [Resend pricing](https://resend.com/pricing). Actual regional quotes, exchange rates,
daily limits, tax and invoice provider pricing must be checked at purchase. A managed
frontend/API/database/worker split generally requires a larger initial recurring budget;
request actual quotes before choosing it. No paid resources were purchased.

## F. External activation

Founder must supply seller identity/contact/VAT details, domain and approved EU hosting;
strong secrets; email account/domain authentication and authorized sandbox recipients;
Stripe test account/prices/portal/webhook; accountant-approved VAT/invoice/Peppol setup;
legal review/DPAs/subprocessors/retention; source reuse approval; security/restore review;
and explicit approval for any external deployment, live payment or real-recipient send.
The [launch checklist](launch-checklist.md) enumerates the gates.

## G. Launch and validation instructions

`cp .env.example .env` → `docker compose up --build` → open localhost:3000 → use the
dry-run outbox CLI to verify an account → complete onboarding → deliberately ingest
official data → refresh/save matches → configure preferences → review digest as admin
→ verify dry run. Worker command: `python -m tenderlens.saas.worker`; `--once` performs
one scheduling/claim/delivery tick. Enable services only with the configuration and
permissions described in [development](development.md), [email](email.md),
[billing](billing.md) and [deployment](deployment.md).

The validation-only local stack was created under Compose project
`tenderlens-codex-stack`, with separate test volumes. Its ports are loopback only.
It is not the production deployment. Stop it without deleting its data using
`docker compose --project-name tenderlens-codex-stack down`.

## H. Known limitations

The matrix is authoritative: no full national coverage, complete TED amendment linking,
human-reviewed Belgian matching benchmark, comprehensive requirement assessment,
full translation, website extraction, full lifecycle mail automation, integrated tax/
Peppol, production recipient sending or public production environment. Run one worker;
SQLAlchemy synchronous work is bounded but not interruptible by the async timeout.
Review provider idempotency windows, rate limits behind proxies, larger-corpus recall,
quota races and downgrade/team policy during controlled pilot testing. The code does
not make the legal/operational launch decisions for the founder.

## I. Next commercial actions

Interview 10–15 Belgian IT/security SMEs through warm introductions, prepare reviewed
source-linked shortlists with permission, recruit 3–5 controlled pilot companies,
measure explicit usefulness and willingness to pay, then complete invoicing/payment/
legal activation before collecting money. Use [commercial playbook](commercial-playbook.md)
templates; no unsolicited campaign or fictional social proof is included.
