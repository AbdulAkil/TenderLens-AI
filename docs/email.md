# Email delivery

The transactional outbox stores escaped responsive table HTML and plain text.
Verification, password reset and welcome messages are essential. Digests and deadline
reminders require verified users, active membership/subscription and notification
preferences. Saved-notice revision updates and explicitly sourced cancellations use
the same outbox. Every logical delivery has a unique key. No fictional tender enters
the production outbox; the test harness uses visibly marked fixtures only.

`EMAIL_PROVIDER=dry_run` is the default. The worker changes approved pending records
to `dry_run` without network delivery. `EMAIL_REQUIRE_APPROVAL=true` holds nonessential
messages at `review` until an internal admin previews and approves them. Preview is
plain text to avoid rendering untrusted source HTML. The approval mode is deployment
configuration; changing it does not automatically release already held messages.

## Sandbox activation

1. Configure a Resend account, sender domain and API key. Validate SPF, DKIM and DMARC.
2. Set `EMAIL_PROVIDER=resend`, `EMAIL_API_KEY`, `EMAIL_FROM` and explicitly list only
   verified test recipients in `EMAIL_SANDBOX_RECIPIENTS`.
3. Obtain approval to send to those recipients before executing provider delivery.
4. Configure the signed Resend webhook at `/api/v1/email/webhook` with
   `EMAIL_WEBHOOK_SECRET`. Svix verifies signatures/timestamps on raw payloads.
5. Review a digest, approve, run the worker, inspect the provider ID and confirm receipt
   on desktop/mobile. Exercise a bounce, complaint and opt-out before any pilot.

An API acceptance is `sent`, not proof of inbox delivery; a signed delivery event can
mark `delivered`. Bounce/complaint events prevent further sends to that recipient.
Do not count a dry run as delivered email. No real recipient was contacted in this
implementation session.

Retries use exponential minute delays, five attempts and stable provider idempotency
keys. Keep one worker. The provider's idempotency retention is finite; review ambiguous
old deliveries manually rather than blindly replaying. Recheck unsubscribe/settings,
membership and account availability immediately before nonessential delivery.

Digests select recently ingested matching notices, sorted by score, at most ten items.
Their daily/week period key respects the user's IANA timezone. Weekly delivery starts
in the first worker period with qualifying results; a user-selectable delivery hour
is not implemented. Exact-notice feedback suppresses dismissed results. Replayed
ingestion can still surface changed records as updates; no completeness promise.

Implemented lifecycle categories: verify, reset, welcome, digest, deadline, saved
notice update/cancellation. Onboarding-completion, trial-expiry, high-score immediate
alerts and dedicated billing/cancellation mail templates are not all automated.
Stripe's configured billing emails can be enabled separately after review. One-click
signed unsubscribe is not implemented; settings provide authenticated opt-out.
Automatic public-recipient email activation remains intentionally unavailable.
