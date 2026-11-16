# Matching and evidence

The deterministic score measures relevance, not eligibility or a probability of
winning. Missing optional profile fields and absent structured tender facts are
`null`, not negative evidence. The score is the weighted mean of observed components:
capability 35, requested skill overlap 20, buyer-country preference 10, comparable
EUR value fit 10 and CPV alignment 10. A services-only perfect capability match is
100/100 and crosses the default 40-point notification preference. Observed term or
classification mismatches contribute zero. Geography/value alone cannot establish
relevance. Certification mentions remain unverified eligibility questions, outside
the relevance denominator; no mention is treated as a proven mandatory condition.

Explicit exclusions, known out-of-range EUR values and configured procedure
mismatches are respected. Missing/non-EUR currency is not compared to EUR bands.
Buyer country is a soft preference, because it does not establish place of
performance. A small EN/NL/FR alias vocabulary helps lexical matching; it is not
universal semantic equivalence. Generic equipment vocabulary and the English
pronoun “it” cannot by themselves create a medical/software capability match.

## Incremental selection

There is no latest-1,000 corpus cut-off. Every locally ingested active candidate is
eligible, irrespective of age. `match_evaluations` persists both accepted and rejected
pairs, with the profile/matcher fingerprint and exact integer tender version.
New/changed candidates are selected by an indexed anti-existence query, ordered by
`updated_at, id`, in batches of 200. A profile or matcher change invalidates its pairs.
This avoids timestamp-watermark races with late commits and equal timestamps.
Successful document processing advances the tender version as evidence changes.
All writes to tender matching evidence must go through the ORM/versioned update path;
external SQL imports must explicitly advance `match_version`.

A company row lock serializes competing recalculations. Each committed batch is
resumable; a retry evaluates only remaining stale pairs. Only a rejected pair or an
inactive notice loses its match. Stale profile/source results are hidden immediately.
The worker fans out profiles using keyset pages and commits continuation jobs until
the corpus is current. HTTP recalculation performs at most five batches, queues the
remainder and reports `pending`; the 100-item response limit does not limit recall.
Digests wait for all profiles in the organization to finish outstanding evaluations.

Memory and per-job scoring work are bounded. Initial/profile-changed evaluation
still traverses all active notices and retained state grows with profile/candidate
pairs. Production-scale storage, query-plan and latency testing remains necessary;
no lexical/CPV prefilter is used that could silently discard a valid candidate.

## Notice lifecycle and deadlines

TED discovery requests notice type, procedure description and entry-deadline fields.
Award/result/modification/completion notices are closed for new-opportunity matching;
planning-only notices are retained as planning records. Existing stored TED projections
with those known types are reclassified by migration 0009. Missing type/deadline stays
unknown and requires source verification. Existing projections without those fields
need a reviewed source refresh/backfill; unknown is not proof of an open competition.

Request-to-participate deadlines take precedence over later tender stages. The
latest known lot entry deadline keeps remaining open lots discoverable. Flattened
search arrays lack lot identity: they are never arbitrarily zipped. Only an
unambiguous single date/time is combined. Date-only deadlines use a conservative UTC
end-of-day boundary, not a claimed exact submission time. Always verify the official
notice and each lot; structured per-lot eligibility/deadlines remain incomplete.
Timezone-bearing timestamps retain their instant in UTC and raw projections preserve
the original offsets.

## Validation and evidence boundaries

[The engineering review](matching-review-2026-11-15.md) records actual results.
The checked-in Belgian fixture contains 15 real TED projections with original
provenance, including Dutch/French titles, English classification summaries, award
and irrelevant controls. Forty-five checks cover three services-only profiles at a
fixed review date; this is a small engineering regression set, not customer-labelled
accuracy evidence. Domain reviewers should label at least 30–50 Belgian notices for
real profiles before tuning thresholds or making commercial precision claims.

Feedback is tenant scoped; irrelevant, not eligible, applied and not interested
suppress that company's notice in digests. It does not retrain weights.
Rules extraction quotes actual source chunks. Optional LLM output must retain
verifiable source evidence and falls back to rules. Unmetered customer query
embeddings remain disabled. Existing retrieval metrics/one Finnish retrieval case
are separate from Belgian matching validation.
