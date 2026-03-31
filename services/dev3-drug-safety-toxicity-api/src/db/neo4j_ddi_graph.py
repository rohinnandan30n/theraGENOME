"""
Neo4j graph database schema and utilities for drug-drug interaction (DDI) graph.
Uses graph structure to model complex drug interactions and find paths/relationships.
"""
from neo4j import AsyncGraphDatabase
from src.config import settings
from typing import Optional, List, Dict


class Neo4jDDIGraph:
    """Neo4j driver for DDI graph operations."""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def close(self):
        """Close the driver connection."""
        await self.driver.close()

    async def init_schema(self):
        """Initialize the Neo4j graph schema for DDI."""
        async with self.driver.session() as session:
            # Create Drug nodes
            await session.run(
                "CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE"
            )
            await session.run(
                "CREATE INDEX drug_name IF NOT EXISTS FOR (d:Drug) ON (d.name)"
            )

            # Create Interaction relationships
            await session.run(
                "CREATE INDEX interaction_type IF NOT EXISTS FOR ()-[r:INTERACTS_WITH]-() ON (r.severity)"
            )

    async def add_drug(self, drug_id: int, name: str, drugbank_id: Optional[str] = None) -> bool:
        """Add a drug node to the graph."""
        async with self.driver.session() as session:
            try:
                await session.run(
                    """
                    MERGE (d:Drug {id: $drug_id})
                    SET d.name = $name, d.drugbank_id = $drugbank_id
                    """,
                    drug_id=drug_id,
                    name=name,
                    drugbank_id=drugbank_id or "",
                )
                return True
            except Exception as e:
                print(f"Error adding drug to Neo4j: {e}")
                return False

    async def add_interaction(
        self,
        drug_a_id: int,
        drug_b_id: int,
        interaction_type: str,
        severity: str,
        description: str,
    ) -> bool:
        """Add a drug-drug interaction edge."""
        async with self.driver.session() as session:
            try:
                await session.run(
                    """
                    MATCH (a:Drug {id: $drug_a_id}), (b:Drug {id: $drug_b_id})
                    MERGE (a)-[r:INTERACTS_WITH]->(b)
                    SET r.interaction_type = $interaction_type,
                        r.severity = $severity,
                        r.description = $description
                    """,
                    drug_a_id=drug_a_id,
                    drug_b_id=drug_b_id,
                    interaction_type=interaction_type,
                    severity=severity,
                    description=description,
                )
                return True
            except Exception as e:
                print(f"Error adding interaction to Neo4j: {e}")
                return False

    async def get_drug_neighbors(self, drug_id: int, max_depth: int = 1) -> List[Dict]:
        """Get interacting drugs within max_depth hops."""
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    """
                    MATCH (d:Drug {id: $drug_id})-[*1..` + str(max_depth) + `]-(neighbor:Drug)
                    RETURN DISTINCT neighbor.id, neighbor.name, neighbor.drugbank_id
                    """,
                    drug_id=drug_id,
                )
                records = await result.data()
                return records
            except Exception as e:
                print(f"Error querying drug neighbors: {e}")
                return []

    async def get_interaction_path(self, drug_a_id: int, drug_b_id: int) -> Optional[List[Dict]]:
        """Find shortest path between two drugs (if they interact transitively)."""
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    """
                    MATCH p = shortestPath((a:Drug {id: $drug_a_id})-[*]-(b:Drug {id: $drug_b_id}))
                    RETURN [n IN nodes(p) | {id: n.id, name: n.name}] as nodes,
                           [r IN relationships(p) | {type: type(r), severity: r.severity}] as edges
                    """,
                    drug_a_id=drug_a_id,
                    drug_b_id=drug_b_id,
                )
                record = await result.single()
                return record.data() if record else None
            except Exception as e:
                print(f"Error finding interaction path: {e}")
                return None

    async def get_high_severity_interactions(self, severity_threshold: str = "severe") -> List[Dict]:
        """Retrieve all interactions with severity >= threshold."""
        severity_order = {"mild": 1, "moderate": 2, "severe": 3}
        threshold = severity_order.get(severity_threshold, 2)

        async with self.driver.session() as session:
            try:
                result = await session.run(
                    """
                    MATCH (a:Drug)-[r:INTERACTS_WITH]-(b:Drug)
                    WHERE r.severity IN ['moderate', 'severe']
                    RETURN a.id, a.name, b.id, b.name, r.interaction_type, r.severity, r.description
                    LIMIT 100
                    """,
                )
                records = await result.data()
                return records
            except Exception as e:
                print(f"Error querying interactions: {e}")
                return []

    async def clear_all(self):
        """Clear all nodes and relationships (use with caution!)."""
        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
