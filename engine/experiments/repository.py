import uuid

import psycopg

from engine.experiments.models import Agent, AgentVersion, Experiment


def get_or_create_agent(conn: psycopg.Connection, name: str, description: str = "") -> Agent:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, description FROM agent WHERE name = %s", (name,))
        row = cur.fetchone()
        if row is not None:
            return Agent(id=row[0], name=row[1], description=row[2])

        agent_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO agent (id, name, description) VALUES (%s, %s, %s)",
            (agent_id, name, description),
        )
    conn.commit()
    return Agent(id=agent_id, name=name, description=description)


def get_or_create_agent_version(
    conn: psycopg.Connection, agent_id: str, version: str, code_ref: str = ""
) -> AgentVersion:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, agent_id, version, code_ref FROM agent_version "
            "WHERE agent_id = %s AND version = %s",
            (agent_id, version),
        )
        row = cur.fetchone()
        if row is not None:
            return AgentVersion(id=row[0], agent_id=row[1], version=row[2], code_ref=row[3])

        version_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO agent_version (id, agent_id, version, code_ref) VALUES (%s, %s, %s, %s)",
            (version_id, agent_id, version, code_ref),
        )
    conn.commit()
    return AgentVersion(id=version_id, agent_id=agent_id, version=version, code_ref=code_ref)


def create_experiment(
    conn: psycopg.Connection,
    agent_version_id: str,
    dataset_id: str,
    model: str,
    config: dict | None = None,
    prompt_version_id: str | None = None,
) -> Experiment:
    experiment_id = str(uuid.uuid4())
    config = config or {}
    with conn.cursor() as cur:
        from psycopg.types.json import Jsonb

        cur.execute(
            "INSERT INTO experiment (id, agent_version_id, dataset_id, model, config, prompt_version_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (experiment_id, agent_version_id, dataset_id, model, Jsonb(config), prompt_version_id),
        )
    conn.commit()
    return Experiment(
        id=experiment_id,
        agent_version_id=agent_version_id,
        dataset_id=dataset_id,
        model=model,
        config=config,
        prompt_version_id=prompt_version_id,
    )


def get_experiment(conn: psycopg.Connection, experiment_id: str) -> Experiment | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, agent_version_id, dataset_id, model, config, status, prompt_version_id "
            "FROM experiment WHERE id = %s",
            (experiment_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return Experiment(
        id=row[0], agent_version_id=row[1], dataset_id=row[2], model=row[3],
        config=row[4], status=row[5], prompt_version_id=row[6],
    )


def list_experiments(conn: psycopg.Connection) -> list[Experiment]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, agent_version_id, dataset_id, model, config, status, prompt_version_id "
            "FROM experiment ORDER BY id ASC"
        )
        rows = cur.fetchall()
    return [
        Experiment(
            id=row[0], agent_version_id=row[1], dataset_id=row[2], model=row[3],
            config=row[4], status=row[5], prompt_version_id=row[6],
        )
        for row in rows
    ]
