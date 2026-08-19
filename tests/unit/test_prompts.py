from engine.prompts.repository import hash_content


def test_hash_is_deterministic_for_same_content():
    content = "You are a helpful service desk agent."
    assert hash_content(content) == hash_content(content)


def test_hash_differs_by_one_character():
    h1 = hash_content("You are a helpful service desk agent.")
    h2 = hash_content("You are a helpful service desk agent!")
    assert h1 != h2


def test_hash_is_64_hex_chars_sha256():
    h = hash_content("anything")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
