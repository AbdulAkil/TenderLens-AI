"""Versioned matching identity, shared by ranking, discovery and delivery."""

import hashlib
import json

MATCHER_VERSION = "evidence-normalized-v2"


def profile_fingerprint(company) -> str:
    fields = (
        "description",
        "services",
        "industries",
        "skills",
        "certifications",
        "preferred_locations",
        "cpv_codes",
        "minimum_contract_value",
        "maximum_contract_value",
        "exclusions",
        "tender_types",
        "languages",
    )
    data = {field: getattr(company, field, None) for field in fields}
    data["matcher_version"] = MATCHER_VERSION
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
