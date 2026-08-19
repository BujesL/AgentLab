import hashlib
import uuid

import psycopg

from engine.prompts.models import PromptVersion


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_or_create_prompt_version(
    conn: psycopg.Connection, name: str, content: str
) -> PromptVersion:
    content_hash = hash_content(content)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, version, content_hash FROM prompt_version WHERE content_hash = %s",
            (content_hash,),
        )
        row = cur.fetchone()
        if row is not None:
            return PromptVersion(id=row[0], name=row[1], version=row[2], content_hash=row[3])

        prompt_id = str(uuid.uuid4())
        version = content_hash[:12]
        cur.execute(
            "INSERT INTO prompt_version (id, name, version, content_hash) VALUES (%s, %s, %s, %s)",
            (prompt_id, name, version, content_hash),
        )
    conn.commit()
    return PromptVersion(id=prompt_id, name=name, version=version, content_hash=content_hash)
