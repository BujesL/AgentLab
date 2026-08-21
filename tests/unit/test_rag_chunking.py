from engine.rag.chunking import chunk_text


def test_splits_on_blank_lines():
    text = "Primeiro parágrafo.\n\nSegundo parágrafo.\n\nTerceiro parágrafo."
    assert chunk_text(text) == [
        "Primeiro parágrafo.",
        "Segundo parágrafo.",
        "Terceiro parágrafo.",
    ]


def test_strips_whitespace_and_drops_empty_chunks():
    text = "  primeiro  \n\n\n\n   \n\nsegundo\n\n"
    assert chunk_text(text) == ["primeiro", "segundo"]


def test_single_paragraph_returns_one_chunk():
    assert chunk_text("um único parágrafo sem quebra") == ["um único parágrafo sem quebra"]


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []
