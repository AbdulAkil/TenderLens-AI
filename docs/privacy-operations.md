# Processing records and review boundaries

Draft technical inventory for counsel; not a legal compliance certification.

| Processing | Data | Purpose | Retention / action |
|---|---|---|---|
| Identity | Email, Argon2 hash, membership | Account access and security | Until reviewed deletion; sessions expire |
| Company matching | Company services/preferences/certifications | Procurement shortlist | Until customer deletion or reviewed retention |
| Engagement | Saved tenders, feedback, audit records | Service operation and customer relevance | Policy review required |
| Delivery | Recipient, template content, delivery state | Account messages and opted-in digests | Completed logs 90 days; pending reviewed manually |
| Payments | Stripe customer/subscription IDs | Test subscription state | Accounting retention to be agreed |
| Public notices | Official metadata, source documents/revisions | Procurement discovery and provenance | Source licence/retention review required |
| Pilot interest | Business contact, message, response permission | Respond to inquiry | Founder to define and implement retention |

Potential processors: chosen EU hosting/backup operator; Stripe for test billing;
Resend only when configured; OpenAI only when explicitly enabled with budget. No
third-party advertising/analytics is installed. Record actual regions, contracts,
DPAs, subprocessors, international transfers and safeguards before activation.

Privacy export covers the user's workspace and preferences. It does not export
password hashes, live session tokens or provider secrets. Organization-owner deletion
requests revoke access immediately; final erasure and external records require the
operator. Individual deletion in a shared organization needs a documented support
workflow to preserve other members' legitimate data. Backup expiry must be included.

The [European Commission rights guidance](https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en)
and [business guidance](https://europa.eu/youreurope/business/governance-and-sustainability/digital-and-data-compliance/data-protection-gdpr/index_en.htm)
provide the review baseline. Determine lawful bases, response deadlines, identity
verification, breach reporting, marketing email rules and necessary-cookie classification
with Belgian/EU counsel. The public privacy/terms/cookie pages remain explicit drafts.
