from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentSource:
    url: str
    media_type: str


def preferred_notice_document(raw_metadata: dict[str, Any]) -> DocumentSource | None:
    """Choose an official TED notice representation without inferring attachments."""
    links = raw_metadata.get("links")
    if not isinstance(links, dict):
        return None
    for format_name, media_type in (
        ("xml", "application/xml"),
        ("htmlDirect", "text/html"),
        ("html", "text/html"),
    ):
        urls = links.get(format_name)
        if not isinstance(urls, dict):
            continue
        for language in ("MUL", "ENG", "eng"):
            url = urls.get(language)
            if isinstance(url, str) and url:
                return DocumentSource(url=url, media_type=media_type)
        for url in urls.values():
            if isinstance(url, str) and url:
                return DocumentSource(url=url, media_type=media_type)
    return None
