import os
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")

from engine.persistence.repository import apply_schema, get_connection
from engine.prompts.repository import get_or_create_prompt_version

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="requires DATABASE_URL (see docs/specs/persistence/plan.md)",
)


@pytest.fixture()
def conn():
    # ADR-006: never TRUNCATE shared tables here — this Neon database also
    # holds the real "service-desk-system-prompt" PromptVersion used by CLI
    # demo experiments. Each test uses unique random content and cleans up
    # only the rows it creates.
    connection = get_connection()
    apply_schema(connection)
    yield connection
    connection.close()


def _cleanup(conn, *content_hashes: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM prompt_version WHERE content_hash = ANY(%s)", (list(content_hashes),)
        )
    conn.commit()


def test_same_content_same_name_returns_same_prompt_version(conn):
    content = f"You are a helpful service desk agent. [{uuid4()}]"
    p1 = get_or_create_prompt_version(conn, name="system-prompt", content=content)
    try:
        p2 = get_or_create_prompt_version(conn, name="system-prompt-again", content=content)
        assert p1.id == p2.id
        assert p1.content_hash == p2.content_hash
    finally:
        _cleanup(conn, p1.content_hash)


def test_different_content_creates_different_prompt_version(conn):
    suffix = uuid4()
    p1 = get_or_create_prompt_version(conn, name="system-prompt", content=f"version one [{suffix}]")
    p2 = get_or_create_prompt_version(conn, name="system-prompt", content=f"version two [{suffix}]")
    try:
        assert p1.id != p2.id
        assert p1.content_hash != p2.content_hash
    finally:
        _cleanup(conn, p1.content_hash, p2.content_hash)


def test_version_field_is_short_hash_prefix(conn):
    p = get_or_create_prompt_version(conn, name="system-prompt", content=f"hello [{uuid4()}]")
    try:
        assert p.version == p.content_hash[:12]
    finally:
        _cleanup(conn, p.content_hash)
