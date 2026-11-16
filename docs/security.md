# Security controls and remaining review

Private routes use a database-backed identity. Opaque 256-bit session tokens are
stored as SHA-256 digests, in HttpOnly SameSite=Lax cookies with a 24-hour default
expiry. Production cookies use Secure. Passwords use pwdlib Argon2. Verification
and reset tokens are single-use, hashed, expire after 30 minutes; reset revokes
sessions. Existing unassigned company profiles remain inaccessible until an operator
audits ownership; no automatic migration into a customer's organization occurs.

Company reads/writes, saved opportunities, matching and feedback check organization
ownership on the server. Owner/admin manage profiles and membership; member access
supports opportunity work. Internal admin is a separate configured verified-email
allowlist. Changing local storage, a UUID or `is_admin` in the UI grants no access.

Cookie-authenticated changes require a trusted Origin. Untrusted Origins are rejected
on all ordinary mutations. Provider webhooks instead validate raw payload signatures
with Stripe/Svix SDKs. CORS uses explicit origins and credentials. Configure a single
origin reverse proxy for production. Authentication limits are shared through the DB;
untrusted X-Forwarded-For cannot bypass them. Current connection-based limits aggregate
users behind a proxy: tune them and review trusted proxy handling before larger rollout.

Official document downloads allow only HTTPS ted.europa.eu:443, no credentials, no
redirects, no environment proxies and a 10 MiB decoded limit. XML uses defusedxml.
Third-party attachments, PDFs and OCR are not automatically processed. These are
reported as unsupported, not silently summarized. Provider text is untrusted data;
LLM facts must reproduce source statements and generated answers must be verbatim
source excerpts or fall back to evidence-only. Prompt defense reduces risk; it is
not a proof against all model attacks. AI defaults off and zero budget.

Live billing keys/events are rejected. Email defaults to dry run; Resend requires an
explicit sandbox recipient allowlist. Bounce/complaint events suppress later sends.
The API omits account-token emails from admin preview. Only the local operator CLI
can inspect dry-run verification/reset links. Never paste them into support tickets.

Production validation rejects sample DB credentials, HTTP site URLs and wildcard or
localhost origins. Containers run without root; DB has no public port; service ports
bind loopback. Set host firewall, HTTPS and infrastructure IAM independently.

## Required before external pilot

PostgreSQL migration/application tests have run locally; add sustained concurrency
and load checks, provider sandbox delivery, Stripe
test Checkout/portal and lifecycle tests, restore rehearsal and independent security
review. Add infrastructure request/body limits and alerts. Recheck dependency audits
on each build. MFA, passkeys, SSO, automated abuse detection and pen testing are not
implemented. No production security certification is claimed.

## Privacy operations

Privacy export is available even for expired subscriptions. Owner deletion requests
revoke organization sessions immediately; final erasure remains an operator workflow
after billing/retention review. Worker removes expired tokens and sessions and old
completed job/delivery records. Counsel must approve full retention and backup policy,
processor contracts, transfers, legal identity and privacy contact before activation.

Incident procedure: stop delivery/ingestion if necessary; revoke compromised sessions
and keys; preserve minimal relevant audit evidence; assess scope and data subjects;
involve counsel and the hosting/provider response contacts; determine notification
obligations; restore from a verified clean backup; document corrective actions.
