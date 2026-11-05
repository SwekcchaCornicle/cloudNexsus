from app.domain.models import ContentBlock
from app.services.chunker import chunk_blocks


def test_chunker_preserves_short_document():
    blocks = [ContentBlock(heading_path=["Intro"], block_type="text", text="A short useful document.")]
    chunks = chunk_blocks(blocks, max_words=10, overlap_words=2, min_words=20)
    assert len(chunks) == 1
    assert "short useful document" in chunks[0][1]


def test_chunker_splits_long_content():
    text = " ".join(f"word{i}" for i in range(45))
    blocks = [ContentBlock(heading_path=["Overview"], block_type="text", text=text)]
    chunks = chunk_blocks(blocks, max_words=20, overlap_words=5, min_words=1)
    assert len(chunks) >= 2
    assert chunks[0][1].split()[-5:] == chunks[1][1].split()[:5]
