from __future__ import annotations

import os

from sagduyu.graph_store import (
    GraphEvidenceWriter,
    Neo4jGraphEvidenceWriter,
    NoopGraphEvidenceWriter,
)
from sagduyu.postgres_store import PostgresModerationStore
from sagduyu.store import InMemoryModerationStore, ModerationStore


def build_moderation_store() -> ModerationStore:
    database_url = os.getenv("SAGDUYU_DATABASE_URL")
    if not database_url:
        return InMemoryModerationStore()
    return PostgresModerationStore(database_url)


def build_graph_writer() -> GraphEvidenceWriter:
    uri = os.getenv("SAGDUYU_NEO4J_URI")
    if not uri:
        return NoopGraphEvidenceWriter()
    username = os.getenv("SAGDUYU_NEO4J_USERNAME")
    password = os.getenv("SAGDUYU_NEO4J_PASSWORD")
    if not username or not password:
        raise ValueError("Neo4j username and password are required when the URI is configured")
    return Neo4jGraphEvidenceWriter(uri, username, password)
