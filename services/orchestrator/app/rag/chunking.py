from __future__ import annotations


def chunk_text(
    text: str,
    *,
    max_chars: int = 1200,
    overlap: int = 120,
) -> list[str]:
    """Proste dzielenie tekstu na nakładające się fragmenty."""
    normalized = (text or "").strip()
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]
    return _overlapping_chunks(normalized, max_chars=max_chars, overlap=overlap)


def _overlapping_chunks(text: str, *, max_chars: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks
