# Founder activation and launch checklist

## Required before an external controlled pilot

- [ ] Run CI on this branch and review every result.
- [x] Apply migrations to disposable PostgreSQL/pgvector.
- [ ] Validate actual legacy-data ownership before importing customer records.
- [ ] Exercise tenant isolation, locks/recovery and the complete workflow on PostgreSQL.
- [ ] Create a verified internal admin, confirm allowlist and member permissions.
- [ ] Establish lawful TED/Belgian reuse and coverage wording; confirm national feed access.
- [ ] Validate matching on reviewed real Belgian EN/NL/FR opportunities.
- [ ] Configure transactional provider/domain SPF, DKIM, DMARC and bounce webhooks.
- [ ] Authorize sandbox recipient sends, deliver an approved digest and verify inbox receipt.
- [ ] Configure Stripe TEST products/prices, signed webhooks, portal and recovery.
- [ ] Exercise checkout, upgrade, downgrade, cancellation, failed payment and replay.
- [ ] Complete accountant review of VAT and structured Belgian B2B invoices/Peppol.
- [ ] Complete legal identity, terms/privacy/cookies, DPA/subprocessors and transfer review.
- [ ] Choose host/domain; approve costs and deployment explicitly.
- [ ] Set unique secrets, HTTPS, firewall, private database, monitored backups.
- [ ] Rehearse restore and document recovery objectives and support ownership.
- [ ] Define retention, deletion completion, incident response and support contact.
- [ ] Verify external-origin cookie/CSRF behavior and tune proxy-aware rate limits.
- [ ] Review accessibility, translations and unsupported attachment/error behavior.

## Before paid production

- [ ] Obtain explicit founder approval for live billing, recipients and public release.
- [ ] Implement/review live-mode activation changes (currently code rejects live keys).
- [ ] Verify tax/invoice integration; publish reviewed commercial renewal/cancellation terms.
- [ ] Review security independently and confirm operational alerting/restore evidence.
- [ ] Confirm no customer testimonials, complete-coverage or matching-quality claims
  exceed actual evidence.

## First customer walkthrough

Create account → inspect dry-run verification or receive authorized sandbox email →
verify → sign in → create company profile → ingest official notices → refresh matches →
review matching reasons/evidence → save tender → choose notifications → run worker →
review digest as admin → approve → verify dry run or authorized sandbox receipt →
open tender link → give feedback → change preferences → prove no duplicate delivery →
perform test checkout and validate webhook entitlements → confirm another tenant cannot
read the profile, saved opportunities, feedback or delivery history.

No launch readiness should be declared until the relevant gates have evidence.
