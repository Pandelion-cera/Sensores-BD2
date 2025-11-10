"""
Populate the `name` property for Neo4j User nodes using the email prefix.

Usage:
    python scripts/backfill_user_names.py
"""
from __future__ import annotations

from app.core.database import db_manager


def main() -> None:
    driver = db_manager.get_neo4j_driver()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User)
            WHERE u.name IS NULL OR u.name = ''
            SET u.name = split(u.email, '@')[0]
            RETURN count(u) AS updated
            """
        )
        updated = result.single()["updated"]
        print(f"[Neo4j] Users updated with name property: {updated}")

    db_manager.close_all()


if __name__ == "__main__":
    main()

