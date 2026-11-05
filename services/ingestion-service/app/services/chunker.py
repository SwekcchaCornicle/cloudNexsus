from __future__ import annotations

import hashlib
from app.domain.models import ContentBlock


def _words(text: str) -> list[str]:
    return text.split()


def chunk_blocks(
    blocks: list[ContentBlock],
    max_words: int = 600,
    overlap_words: int = 80,
    min_words: int = 20,
) -> list[tuple[list[str], str, int]]:
    if max_words <= 0 or overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("Require max_words > overlap_words >= 0.")

    chunks: list[tuple[list[str], str, int]] = []
    current_words: list[str] = []
    current_heading: list[str] = []

    def flush() -> None:
        nonlocal current_words
        if len(current_words) >= min_words:
            chunks.append((current_heading.copy(), " ".join(current_words), len(current_words)))
        current_words = []

    for block in blocks:
        words = _words(block.text)
        if not words:
            continue

        if current_words and block.heading_path != current_heading:
            flush()
        current_heading = block.heading_path.copy()

        cursor = 0
        while cursor < len(words):
            capacity = max_words - len(current_words)
            take = min(capacity, len(words) - cursor)
            current_words.extend(words[cursor : cursor + take])
            cursor += take

            if len(current_words) >= max_words:
                completed = current_words.copy()
                flush()
                current_words = completed[-overlap_words:] if overlap_words else []

    if current_words:
        flush()

    # Preserve short but meaningful documents rather than returning no chunks.
    if not chunks and blocks:
        combined = " ".join(block.text for block in blocks).strip()
        if combined:
            chunks.append((blocks[0].heading_path.copy(), combined, len(_words(combined))))

    return chunks


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
