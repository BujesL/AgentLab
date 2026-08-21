import requests

EMBEDDING_DIM = 768


def embed(text: str, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434", timeout: int = 60) -> list[float]:
    response = requests.post(
        f"{base_url}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=timeout,
    )
    response.raise_for_status()
    embedding = response.json()["embedding"]
    if len(embedding) != EMBEDDING_DIM:
        raise ValueError(
            f"expected embedding of dim {EMBEDDING_DIM} from model {model!r}, "
            f"got {len(embedding)} — schema.sql assumes vector(768)"
        )
    return embedding
