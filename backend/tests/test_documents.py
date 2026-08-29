from tenderlens.documents.chunking import chunk_text
from tenderlens.documents.extraction import extract_text
from tenderlens.documents.source import preferred_notice_document
from tenderlens.models.document import DocumentChunk


def test_extracts_xml_and_chunks_deterministically() -> None:
    text = extract_text(
        b"<notice><title>Open procedure</title><requirement>Submit a signed offer.</requirement></notice>",
        "application/xml",
        "https://ted.europa.eu/en/notice/1-2026/xml",
    )

    chunks = chunk_text(text, max_characters=30, overlap_characters=5)

    assert "Open procedure" in text
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.content for chunk in chunks)


def test_prefers_official_multilingual_xml_url() -> None:
    source = preferred_notice_document(
        {"links": {"xml": {"MUL": "https://ted.europa.eu/en/notice/1-2026/xml"}}}
    )

    assert source is not None
    assert source.media_type == "application/xml"


def test_document_chunks_use_database_timestamp_defaults() -> None:
    assert DocumentChunk.__table__.c.created_at.server_default is not None
