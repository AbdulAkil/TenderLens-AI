from __future__ import annotations

from html.parser import HTMLParser

from defusedxml import ElementTree


class UnsupportedDocumentTypeError(ValueError):
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._suppressed_depth:
            self._suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._suppressed_depth and data.strip():
            self.parts.append(data.strip())


def extract_text(content: bytes, media_type: str | None, source_url: str) -> str:
    normalized_type = (media_type or "").split(";", 1)[0].lower()
    if normalized_type in {"application/xml", "text/xml"} or source_url.endswith("/xml"):
        return _extract_xml(content)
    if normalized_type == "text/html" or source_url.endswith("/html"):
        return _extract_html(content)
    raise UnsupportedDocumentTypeError(
        f"No text extractor registered for {normalized_type or 'unknown document type'}"
    )


def _extract_xml(content: bytes) -> str:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise ValueError("Source XML is not well-formed") from error
    return "\n".join(text.strip() for text in root.itertext() if text and text.strip())


def _extract_html(content: bytes) -> str:
    parser = _VisibleTextParser()
    parser.feed(content.decode("utf-8", errors="replace"))
    return "\n".join(parser.parts)
