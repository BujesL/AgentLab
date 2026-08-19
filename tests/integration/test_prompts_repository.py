import os

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
    connection = get_connection()
    apply_schema(connection)
    with connection.cursor() as cur:
        cur.execute("TRUNCATE prompt_version RESTART IDENTITY CASCADE")
    connection.commit()
    yield connection
    connection.close()


def test_same_content_same_name_returns_same_prompt_version(conn):
    content = "You are a helpful service desk agent."
    p1 = get_or_create_prompt_version(conn, name="system-prompt", content=content)
    p2 = get_or_create_prompt_version(conn, name="system-prompt-again", content=content)

    assert p1.id == p2.id
    assert p1.content_hash == p2.content_hash


def test_different_content_creates_different_prompt_version(conn):
    p1 = get_or_create_prompt_version(conn, name="system-prompt", content="version one")
    p2 = get_or_create_prompt_version(conn, name="system-prompt", content="version two")

    assert p1.id != p2.id
    assert p1.content_hash != p2.content_hash


def test_version_field_is_short_hash_prefix(conn):
    p = get_or_create_prompt_version(conn, name="system-prompt", content="hello")
    assert p.version == p.content_hash[:12]
