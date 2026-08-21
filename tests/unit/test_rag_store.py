from engine.rag.store import _to_vector_literal


def test_vector_literal_format():
    assert _to_vector_literal([0.1, 0.2, -0.3]) == "[0.1,0.2,-0.3]"


def test_vector_literal_empty():
    assert _to_vector_literal([]) == "[]"
