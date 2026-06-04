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

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
