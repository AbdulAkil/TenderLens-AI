# Matching and evidence

The retained deterministic formula weights capability terms 35%, skills 20%,
certification signals 15%, country preference 10%, value fit 10%, CPV 10%.
Unknown inputs earn zero evidence credit, rather than positive eligibility credit.
The result is an experimental relevance score, not a probability or legal decision.

Candidates exclude expired deadlines, explicit closed/cancelled status, configured
exclusions, known out-of-range values and configured procedure mismatches. Country
filtering uses available buyer country, not verified place of performance. Missing
values stay unknown. A small normalized EN/NL/FR alias vocabulary covers software,
cybersecurity, development, data, maintenance, electrical work and renovation. It
does not provide universal multilingual semantic equivalence. Existing optional
vector infrastructure remains, but unmetered customer query embeddings are disabled.

Matching processes at most the latest 1,000 candidates per profile and skips unchanged
profile/notice pairs. Stale excluded matches are removed. This bounds pilot work and
limits recall on larger corpora. A larger deployment needs cursor-based batches and
candidate retrieval evaluation before changing that limit. Known certifications
are mentions, not automatically confirmed mandatory conditions. Reasons and blockers
are inspectable; manual eligibility verification is always required.

Feedback belongs to a company within its organization. Irrelevant, not eligible,
already applied and not interested suppress the exact notice in future digests.
Feedback does not currently retrain weights or infer generalized preferences.

Rules extraction quotes source text; optional LLM extraction only retains statements
found in actual chunks. Source chunk IDs and the supporting document are retained.
Provider failure falls back to rules. Q&A returns evidence-only when unavailable or
when generated text cannot be verified verbatim. No unsupported citations are added.

`evaluation.metrics` includes precision@K, false-positive rate and useful-match rate,
with empty/undefined cases explicit. The existing reviewed dataset has one Finnish
retrieval case; it is not a reviewed Belgian matching benchmark. No precision or
commercial performance claim follows from unit fixtures. Before tuning thresholds,
have domain reviewers label at least 30–50 Belgian EN/NL/FR notices for multiple real
profiles; record disagreements, false negatives, and eligibility uncertainty. The
default threshold 40 is an adjustable starting preference, not a validated boundary.
