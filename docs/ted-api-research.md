# TED API research — 29 August 2026

## Decision

TenderLens will use the official **TED API v3 Search API** for published-notice discovery. Its production base URL is `https://api.ted.europa.eu`; the endpoint is `POST /v3/notices/search`.

This is the appropriate first source because it is the EU Publications Office's public discovery interface, is designed for data reusers, and does not require authentication for published notices. The separate publication, validation, and conversion APIs are not required for TenderLens ingestion.

## Verified capabilities

| Concern | TED Search API v3 capability | TenderLens decision |
| --- | --- | --- |
| Authentication | Anonymous for published notices | No API key required for ingestion |
| Search | `POST /v3/notices/search` with an expert `query` | Isolate query construction from HTTP transport |
| Fields | `fields` selects returned data | Request only needed identity/metadata fields |
| Pagination | `PAGE_NUMBER` and `ITERATION` modes | Use iteration for full backfills; page mode for bounded runs |
| Limits | 250 notices/page; pagination mode max 15,000 documents; iteration has no total-document cap; both cap 10,000 fields/page | Client enforces 1–250 page size |
| Notice formats | Search results include format/language URLs; direct TED links serve HTML, PDF, signed PDF, and XML | Persist canonical notice/document URLs for future acquisition |
| Rate limits | Official reuse material documents fair use but does not publish a numeric Search API request quota | Retry 429 using `Retry-After`, exponential backoff, and structured logs; do not assume a numeric limit |

## Important constraints

- Search is not available in the eForms Preview environment, and only published notices are returned.
- The requested fields determine the result shape. The normalizer therefore preserves the raw payload and only requires identity/title aliases explicitly asked for by the ingestion query.
- TED provides eForms and legacy TED-schema notice material. Document processing must retain source type and not assume one XML structure.
- Publication APIs use API keys and apply to an organisation's own submissions; TenderLens will not use them.

## Implemented TED discovery projection

The controlled ingestion runner requests only documented Search fields: `publication-number`, `notice-title`, `title-proc`, `buyer-name`, `buyer-country`, `publication-date`, `deadline`, `procedure-type`, `classification-cpv`, `estimated-value-proc`, and `estimated-value-cur-proc`.

TED Search returns a notice projection, not a relational lot record. In particular, titles and buyer names are language-keyed maps, CPVs can repeat, and format URLs are returned under `links`. TenderLens selects a display value deterministically (English when available, then the first supplied language), deduplicates CPV codes, preserves the raw response, and never zips repeated fields into inferred lot data.

## Official references

- [TED API v3 overview](https://docs.ted.europa.eu/api/latest/)
- [Search API documentation](https://docs.ted.europa.eu/api/latest/search.html)
- [Search API pagination and limits](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html)
- [TED public API Swagger interface](https://api.ted.europa.eu/swagger-ui/index.html)
- [TED developer corner: direct notice formats and bulk data](https://ted.europa.eu/en/simap/developers-corner-for-reusers)
