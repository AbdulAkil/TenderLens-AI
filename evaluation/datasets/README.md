# Evaluation datasets

Add only source-permitted TED notice/document examples with manually reviewed answers and source locations. Do not put synthetic performance results here.
Each JSONL record is a reviewed, source-specific retrieval case. `source_id` must match the TED
notice identifier stored by ingestion. `expected_evidence_terms` are terms that must occur together
in a relevant source chunk; the evaluator uses them to calculate Recall@1, Recall@5, and MRR without
calling a paid model. Reports are generated locally and are not committed as claimed benchmarks.
