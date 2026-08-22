from __future__ import annotations

from typing import Protocol

from neo4j import Driver, GraphDatabase

from sagduyu.models import CoordinationAlert


class GraphEvidenceWriter(Protocol):
    mode: str

    def write_alerts(self, alerts: list[CoordinationAlert]) -> None: ...

    def close(self) -> None: ...


class NoopGraphEvidenceWriter:
    mode = "disabled"

    def write_alerts(self, alerts: list[CoordinationAlert]) -> None:
        return None

    def close(self) -> None:
        return None


class Neo4jGraphEvidenceWriter:
    mode = "neo4j"

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        *,
        driver: Driver | None = None,
    ) -> None:
        self.driver = driver or GraphDatabase.driver(uri, auth=(username, password))
        self.driver.verify_connectivity()

    def write_alerts(self, alerts: list[CoordinationAlert]) -> None:
        with self.driver.session() as session:
            for alert in alerts:
                session.run(
                    """
                    MERGE (e:EvidenceAlert {id: $alert_id})
                    SET e.risk_score = $risk_score,
                        e.risk_level = $risk_level,
                        e.engine_version = $engine_version,
                        e.synthetic = $synthetic,
                        e.updated_at = datetime()
                    WITH e
                    UNWIND $account_ids AS account_id
                    MERGE (a:Account {id: account_id})
                    MERGE (a)-[:IN_EVIDENCE {alert_id: $alert_id}]->(e)
                    """,
                    alert_id=alert.alert_id,
                    risk_score=alert.risk_score,
                    risk_level=alert.risk_level.value,
                    engine_version=alert.engine_version,
                    synthetic=alert.synthetic,
                    account_ids=alert.account_ids,
                ).consume()
                session.run(
                    """
                    UNWIND $pairs AS pair
                    MERGE (left:Account {id: pair.left})
                    MERGE (right:Account {id: pair.right})
                    MERGE (left)-[r:COORDINATES_WITH {
                        alert_id: $alert_id,
                        peer_key: pair.right
                    }]->(right)
                    SET r.strength = pair.strength,
                        r.engine_version = $engine_version,
                        r.updated_at = datetime()
                    """,
                    alert_id=alert.alert_id,
                    engine_version=alert.engine_version,
                    pairs=[
                        {"left": left, "right": right, "strength": strength}
                        for left, right, strength in alert.graph.strongest_pairs
                    ],
                ).consume()

    def close(self) -> None:
        self.driver.close()
