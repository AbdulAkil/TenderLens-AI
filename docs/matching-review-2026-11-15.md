# Commercial-pilot engineering review — 2026-11-15

Scope: first-customer matching correctness, recall, digest freshness and CI reliability
on `feat/commercial-pilot`. No public deployment, live payment, paid AI request or
real-recipient email was activated.

## Findings and fixes

| Finding | Consequence | Implemented fix |
|---|---|---|
| Root Ruff treated `tenderlens` differently from backend Ruff | Backend CI failed I001 at `scripts/pilot_test_server.py:14` | Shared root configuration and explicit first-party import classification; I001 remains enabled |
| Optional missing profile data scored as zero against a fixed denominator | A perfect services-only match could miss the 40-point digest preference | Normalize by observed evidence; `null` unknowns, zero observed mismatch; eligibility remains unverified |
| Latest-1,000 selection and corpus-wide stale deletion | Older active notices and valid prior matches could disappear | Persist every evaluated pair, source version and profile/matcher fingerprint; resumable 200-notice batches and worker continuations |
| Ingestion time defined digest freshness | Onboarding missed older opportunities; replays/updates could repeat notices | Durable recipient/organization/notice assignments independent of publication time and delivery-log retention |
| Approved drafts could outlive their evidence | Cancelled, expired, dismissed or newly unsuitable opportunities could be sent | Final source/profile/version/deadline/preference checks; regenerate unattempted stale drafts, hold ambiguous attempted sends |
| TED search projection omitted notice type and current entry deadlines | Award notices appeared active; legitimate request deadlines were unknown | Request type, description and deadline fields; exclude awards/planning-only records from new opportunity matching, preserve UTC instants |
| Earliest lot deadline expired the entire notice | A later open lot could be suppressed | Keep latest known entry deadline; prioritize requests to participate; verify each lot at source |
| Generic vocabulary/English “it” could produce false capability hits | Broadcast equipment appeared medical; pronoun appeared to mean IT | Ignore generic equipment terms and distinguish uppercase IT acronym from the pronoun |
| Browser harness shared one SQLite connection between concurrent requests | Repeatable local API resets during browser workflow | Ephemeral file-backed SQLite with separate connections; clean browser suite passes |

Migration `20261115_0009` adds evaluation state, optimistic source versions, selection
index and durable digest assignments. It backfills known retained digest workspace
links, reclassifies known TED awards/planning records, and intentionally refuses a
history-destroying downgrade. Back up before applying to an actual customer database.
No customer database was migrated during this review.

## Exact local CI results

| Check | Result |
|---|---|
| `ruff check backend scripts` | Passed, I001 enabled |
| `ruff format --check backend` | Passed |
| SQLite `pytest backend/tests -q` | **86 passed, 1 skipped** (PostgreSQL-only migration regression) |
| PostgreSQL 16 `TEST_DATABASE_URL=... pytest backend/tests -q` | **87 passed** in isolated per-test schemas |
| Fresh PostgreSQL `alembic upgrade head`, repeated upgrade, schema acceptance | Passed through **0009** |
| Retained-data migration regression | Passed: historical receipt preserved, existing award closed, unavailable profile evidence left null |
| Frontend lint, typecheck, production build | Passed |
| Browser `npm run test:e2e` | **2 passed**, including verified customer workflow and responsive checks |
| `npm audit` | **0 known vulnerabilities** |
| `python -m pip_audit` | **0 known vulnerabilities**; local application package is not on PyPI and is skipped |
| Compose configuration and API/worker/frontend image builds | Passed; build only, no public deployment |

An upstream Starlette/httpx TestClient deprecation warning remains. Migration
inspection emits a pgvector type-reflection warning; schema/vector acceptance passes.
Two initial local browser attempts failed with API connection resets; the shared
SQLite connection was removed before the successful final run. No failed test is
counted as passing. Hosted CI must be checked for the pushed commit separately.

Regression coverage includes 1,006 active candidates with a 300-day-old opportunity,
zero rescoring of unchanged pairs, one-notice source updates, equal timestamps,
profile changes including previous rejections, interruption/restart, continuation
retries, stale result hiding, expiry, unknown currency, older-ingestion onboarding,
10-item overflow, delivery-log cleanup and stale approved drafts.

## Real Belgian validation

Source: [official TED Search API](https://api.ted.europa.eu/v3/notices/search).
The [notice type vocabulary](https://docs.ted.europa.eu/eforms/latest/reference/code-lists/notice-type.html)
and [search field documentation](https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html)
were checked against the real projections.

A live bounded query `buyer-country = BEL AND publication-date >= 20261101`, scope
ALL, returned **30 of 661** matching publications. It inserted **30**, then identical
replay returned **0 inserts, 0 updates, 30 unchanged**. Discovery reported
`complete=false` as expected for this deliberately bounded sample; this is not a
claim of complete Belgian market ingestion.

In a disposable PostgreSQL schema, a verified software SME supplying **only**
`services=["software"]` matched the real VDAB planning-tool notice
[757153-2026](https://ted.europa.eu/en/notice/-/detail/757153-2026) at **100/100**.
Its actual request deadline was retained as **2026-12-03 10:00 UTC / 11:00 Brussels**.
Award notices 756781-2026 and 757157-2026 were excluded despite software capability
hits. The workflow then created **1 review digest**, passed authenticated admin
preview/approval, reached **dry_run** with **no provider ID**, and created **0 duplicate
digests** on replay. The isolated schema was removed after the check.

The checked-in [15-notice fixture](../evaluation/datasets/belgian-matching-review-20261115.json)
retains original TED projections, dates, languages and source links. It exercises
**45 engineering-reviewed opportunity checks** across services-only software,
construction and medical equipment profiles, at a frozen 2026-11-15 review date:
**45/45 pass** (8 expected active opportunities across profiles, 37 negative controls).
The set includes awards, unrelated equipment, and an expired ecological study.
Dates are not moved into the future to make a sample look active. The automated
fixture workflow verifies ingestion, unchanged replay, matching, digest creation,
admin preview/approval and dry-run delivery on both database implementations.

## Remaining customer-launch blockers and limits

- This is a small engineering regression sample, not customer-labelled precision,
  recall, legal eligibility or bid-success validation. Obtain domain review of real
  customer profiles and 30–50 notices before making commercial quality claims.
- Full permitted Belgian national e-Procurement integration and complete historical
  TED/source refresh are unresolved. Existing records missing type/deadline data
  need reviewed backfill; unknown is not guaranteed open. Cross-publication award,
  cancellation and corrigendum chains can leave an older competition uncertain.
- Flattened TED lot arrays do not provide full lot identity, eligibility or precise
  deadlines in every projection. Verify the official record. Unknown lots/deadlines
  remain a source-quality limitation rather than invented certainty.
- Incremental jobs bound memory/work and preserve recall over the ingested corpus;
  initial/profile-changed scans and evaluation storage still grow with corpus and
  profile count. Sustained load, query-plan, backup/restore and operational alerting
  validation remain before a larger rollout. One worker remains the supported mode.
- Real email provider sandbox receipt, deliverability and bounce tests, Stripe test
  checkout, legal/accounting review and independent security/restore exercises
  remain from the original readiness report. No real-recipient email, live payment
  or public deployment was attempted.
