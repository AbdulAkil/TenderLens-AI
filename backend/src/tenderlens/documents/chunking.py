from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    content: str
    chunk_index: int
    section: str | None = None


def chunk_text(
    text: str, *, max_characters: int = 1_200, overlap_characters: int = 180
) -> list[TextChunk]:
    """Create deterministic, whitespace-normalized chunks without model tokenization."""
    if max_characters <= overlap_characters:
        raise ValueError("max_characters must exceed overlap_characters")
    paragraphs = [" ".join(part.split()) for part in text.split("\n") if part.strip()]
    chunks: list[TextChunk] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_characters:
            if current:
                chunks.append(TextChunk(content=current, chunk_index=len(chunks)))
                current = ""
            chunks.extend(
                _split_long_paragraph(paragraph, max_characters, overlap_characters, len(chunks))
            )
            continue
        proposed = f"{current}\n{paragraph}".strip()
        if current and len(proposed) > max_characters:
            chunks.append(TextChunk(content=current, chunk_index=len(chunks)))
            current = current[-overlap_characters:] + "\n" + paragraph
        else:
            current = proposed
    if current:
        chunks.append(TextChunk(content=current, chunk_index=len(chunks)))
    return chunks


def _split_long_paragraph(
    paragraph: str,
    max_characters: int,
    overlap_characters: int,
    initial_index: int,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    start = 0
    while start < len(paragraph):
        end = min(start + max_characters, len(paragraph))
        if end < len(paragraph):
            boundary = paragraph.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(
            TextChunk(content=paragraph[start:end], chunk_index=initial_index + len(chunks))
        )
        if end == len(paragraph):
            break
        start = max(end - overlap_characters, start + 1)
    return chunks
