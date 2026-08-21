import psycopg

from engine.rag.chunking import chunk_text
from engine.rag.embeddings import embed


def _to_vector_literal(embedding: list[float]) -> str:
    # No pgvector-python dependency added for this MVP increment — pgvector
    # accepts a plain "[v1,v2,...]" text literal cast with ::vector.
    return "[" + ",".join(repr(v) for v in embedding) + "]"


def ingest_document(
    conn: psycopg.Connection, source: str, text: str, embed_model: str = "nomic-embed-text"
) -> int:
    chunks = chunk_text(text)
    with conn.cursor() as cur:
        for index, chunk in enumerate(chunks):
            vector = _to_vector_literal(embed(chunk, model=embed_model))
            cur.execute(
                """
                INSERT INTO document_chunk (source, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s::vector)
                """,
                (source, index, chunk, vector),
            )
    conn.commit()
    return len(chunks)


def retrieve(
    conn: psycopg.Connection, query: str, k: int = 3, embed_model: str = "nomic-embed-text"
) -> list[str]:
    vector = _to_vector_literal(embed(query, model=embed_model))
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content FROM document_chunk
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vector, k),
        )
        return [row[0] for row in cur.fetchall()]


class PgVectorRetriever:
    """Retriever backed by document_chunk in Postgres/pgvector.

    A thin adapter around store.retrieve() so AgentRunner depends only on the
    `retrieve(query, k) -> list[str]` shape, not on psycopg/connection details —
    keeps AgentRunner testable with a fake retriever, no DB/Ollama required.
    """

    def __init__(self, conn: psycopg.Connection, embed_model: str = "nomic-embed-text") -> None:
        self.conn = conn
        self.embed_model = embed_model

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        return retrieve(self.conn, query, k=k, embed_model=self.embed_model)
