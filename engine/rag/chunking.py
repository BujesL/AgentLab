def chunk_text(text: str) -> list[str]:
    """Split text into paragraph chunks (blank-line separated).

    No overlap, no token-aware sizing — chunking sophistication is explicitly
    out of scope for this MVP increment (see docs/specs/rag-pipeline/spec.md).
    """
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]
