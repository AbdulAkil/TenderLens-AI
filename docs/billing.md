# Billing

Plans are server-defined in `saas/plans.py`. `PLANS_JSON` can replace their complete
configuration: each entry needs name, monthly_eur, profiles, members and saved; optional
daily, analysis, comparison, export booleans default false. Default prices are €29,
€79 and €149 excluding applicable tax, hypotheses to validate with customers.

Signup grants a configurable 14-day Professional trial without a card. Expired trials,
canceled/incomplete/past-due subscriptions cannot create profiles, save new opportunities,
recalculate matches or use paid analysis. Existing private data and privacy export
remain available. Organization locks serialize profile/member/saved quotas. Downgrades
preserve records; limits apply to additions. Only manager roles can open billing.

## Stripe test configuration

1. Create a Stripe test account and three EUR recurring monthly Prices.
2. Set `STRIPE_SECRET_KEY=sk_test_...`, each `STRIPE_*_PRICE`, and
   `STRIPE_WEBHOOK_SECRET=whsec_...`. Never put them in NEXT_PUBLIC variables.
3. Configure a test Customer Portal with plan changes, cancellation, invoices and
   payment-method management. Configure recovery/dunning in Stripe.
4. Forward subscription created/updated/deleted, Checkout completed, invoice paid
   and invoice payment_failed to `/api/v1/billing/webhook`.
5. Open `/billing`, use a test Checkout, verify the signed event changes access,
   change plan, cancel at period end, simulate payment failure and replay events.
6. Test invoice history and return URLs on the actual domain. Never infer success
   from the browser return page; the signed webhook is the source of access state.

Webhook processing checks raw-body signatures, rejects live events, serializes event
IDs on PostgreSQL, stores processed IDs transactionally, verifies customer/organization
ownership, maps server-configured prices, and refetches current subscription state to
avoid stale event rollbacks. Mock tests cover signed replay and ownership. Real
provider Checkout/portal has not been exercised without credentials.

## Tax and legal activation gate

Tax IDs and billing addresses are collected. Stripe automatic tax calculation is not
enabled and no tax-compliance claim is made. A Belgian accountant must confirm B2B
classification, domestic VAT, intra-EU reverse charge/VIES evidence, invoice numbering,
retention and the applicable structured invoice integration.

[Belgium's official guidance](https://einvoice.belgium.be/en/FAQ/general-questions-b2b)
states that structured B2B e-invoicing applies to in-scope Belgian VAT business
transactions from 1 January 2026. An emailed Stripe PDF is not an implemented Peppol
integration. Select and test an appropriate accounting/Peppol provider before live
Belgian billing. [Official software guidance](https://einvoice.belgium.be/en/article/software-solutions-sending-receiving-and-processing-electronic-invoices)
describes connected solutions. Confirm exceptions with the accountant.

Live keys are deliberately rejected. Removing that guard requires explicit founder
authorization, legal/tax approval, a verified integration and a separate reviewed change.
Subscription obligations, renewal/cancellation copy, seller identity and terms remain
legal review items. See [Stripe subscriptions](https://docs.stripe.com/billing/subscriptions/webhooks).
