# Procurement sources — checked 2026-11-15

## TED

Official public Search API: `POST https://api.ted.europa.eu/v3/notices/search`.
Anonymous published-notice searches are documented by the
[TED developer corner](https://ted.europa.eu/en/simap/developers-corner-for-reusers).
The [official OpenAPI UI](https://api.ted.europa.eu/swagger-ui/index.html) identifies
the v3 route. [Pagination documentation](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html)
describes page-number and iteration modes, up to 250 notices/page and field limits.
The client uses iteration, bounded batches, retry/backoff, pacing and repeated-token
detection. A bounded real search with the existing projection returned HTTP 200
during implementation. This validates transport/projection, not completeness.

Original notice JSON and canonical source URLs are preserved. Same-payload replays
do not update timestamps or generate revisions. Changed payloads retain snapshots
and changed fields. Publication-number identity is unique. Linking different TED
publication numbers into one procurement procedure/version chain is still incomplete.
Cancellation is only explicit where the source/import supplies confirmed status;
unknown status is not called open. Do not infer cancellation from a title.

Date-time offsets are preserved. Missing/naive exact times remain unknown. Date-only
source dates use the existing conservative UTC date boundary, with raw precision
preserved; do not interpret midnight as an official submission time. Buyer country
is not necessarily the contract's place of performance. Detailed geography needs
additional official fields before claiming regional eligibility.

Current scheduler replays a rolling three-day publication window each hour and fails
visibly when its notice limit truncates the response. Use separate daily backfills
and investigate late corrections beyond this window. This is not a completeness SLA.

## Belgian e-Procurement

[BOSA's official application page](https://bosa.belgium.be/en/applications/e-procurement)
identifies the national platform. Automated access to the documentation page was
met with a human verification challenge during research. It was not bypassed.
No permitted national API/feed contract was verified, so no speculative scraper was
implemented. TED does not cover every below-threshold Belgian opportunity.

An internal admin can submit a reviewed, legally reusable notice to
`POST /api/v1/admin/imports`. It accepts recognized official HTTPS source URLs,
timezone-aware dates and explicit unknown values, preserves the imported payload,
records the actor, and performs no remote fetch. Confirm reuse permission first.
Never import confidential or access-controlled procurement materials without authority.

## Reuse and attribution

Keep official source identity, publication number, source link, raw metadata and
retrieval timestamp. The [TED data reuse page](https://ted.europa.eu/en/help/data-reuse)
describes official reuse channels. Legal review must confirm applicable reuse notices,
attribution and third-party document rights; public availability alone is not a
universal licence. No affiliation or endorsement by TED/BOSA is represented.
