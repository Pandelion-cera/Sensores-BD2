"""
Utility script to rebuild role-based permissions in Neo4j.

It removes legacy User→Process permission edges, recreates Role→Process
relationships for execution, and adds User→Process edges for request
capabilities. Use after seeding data or when permissions drift from the
expected schema.
"""
from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from typing import Dict, List, Set

from app.core.database import db_manager

EXECUTOR_ROLES = {"tecnico", "administrador"}
REQUEST_ROLES = {"usuario"}

# If True, every role in REQUEST_ROLES will be allowed to request every process,
# even if historic data does not include explicit permissions.
ASSIGN_ALL_PROCESSES_TO_REQUEST_ROLES = True

# If True and no historic execution data is found for a role in EXECUTOR_ROLES,
# grant execution rights over all processes.
ASSIGN_ALL_PROCESSES_TO_EXECUTOR_ROLES = False

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewire Neo4j permissions to be role-based."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log the operations that would be performed.",
    )
    return parser.parse_args()


def fetch_all_process_ids(mongo_db) -> Set[str]:
    processes = mongo_db["processes"].find({}, {"_id": 1})
    return {str(doc["_id"]) for doc in processes}


def fetch_user_roles(session) -> Dict[str, List[str]]:
    result = session.run(
        """
        MATCH (u:User)-[:HAS_ROLE]->(r:Role)
        RETURN u.id AS user_id, collect(DISTINCT r.name) AS roles
        """
    )
    return {record["user_id"]: record["roles"] for record in result}


def fetch_user_processes(session) -> Dict[str, List[str]]:
    result = session.run(
        """
        MATCH (u:User)-[:CAN_EXECUTE]->(p:Process)
        RETURN u.id AS user_id, collect(DISTINCT p.id) AS process_ids
        """
    )
    return {record["user_id"]: record["process_ids"] for record in result}


def build_mappings(
    user_roles: Dict[str, List[str]],
    user_processes: Dict[str, List[str]],
    all_process_ids: Set[str],
) -> tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    role_execute_map: Dict[str, Set[str]] = defaultdict(set)
    role_request_map: Dict[str, Set[str]] = defaultdict(set)

    for user_id, roles in user_roles.items():
        processes = set(user_processes.get(user_id, []))
        if not processes:
            continue
        for role in roles:
            if role in EXECUTOR_ROLES:
                role_execute_map[role].update(processes)
            if role in REQUEST_ROLES:
                role_request_map[role].update(processes)

    if ASSIGN_ALL_PROCESSES_TO_REQUEST_ROLES and all_process_ids:
        for role in REQUEST_ROLES:
            role_request_map[role].update(all_process_ids)

    if ASSIGN_ALL_PROCESSES_TO_EXECUTOR_ROLES and all_process_ids:
        for role in EXECUTOR_ROLES:
            if role not in role_execute_map or not role_execute_map[role]:
                role_execute_map[role] = set(all_process_ids)

    return role_execute_map, role_request_map


def clear_existing_edges(session, dry_run: bool) -> None:
    statements = [
        "MATCH (:User)-[r:CAN_EXECUTE]->(:Process) DELETE r",
        "MATCH (:Role)-[r:CAN_EXECUTE]->(:Process) DELETE r",
        "MATCH (:User)-[r:CAN_REQUEST]->(:Process) DELETE r",
        "MATCH (:Role)-[r:CAN_REQUEST]->(:Process) DELETE r",
    ]
    if dry_run:
        logger.info("Dry-run: skipping deletion of existing permission edges.")
        return
    for stmt in statements:
        session.run(stmt)


def create_role_edges(
    session,
    relationship: str,
    mapping: Dict[str, Set[str]],
    dry_run: bool,
) -> None:
    cypher = f"""
        MATCH (r:Role {{name: $role_name}})
        MATCH (p:Process {{id: $process_id}})
        MERGE (r)-[:{relationship}]->(p)
    """
    for role_name, process_ids in mapping.items():
        for process_id in process_ids:
            if dry_run:
                logger.info(
                    "Dry-run: MERGE (:Role {name:%s})-[:%s]->(:Process {id:%s})",
                    role_name,
                    relationship,
                    process_id,
                )
                continue
            session.run(cypher, role_name=role_name, process_id=process_id)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    mongo_db = db_manager.get_mongo_db()
    driver = db_manager.get_neo4j_driver()

    all_process_ids = fetch_all_process_ids(mongo_db)
    logger.info("Discovered %s processes.", len(all_process_ids))

    with driver.session() as session:
        user_roles = fetch_user_roles(session)
        user_processes = fetch_user_processes(session)

        logger.info("Loaded %s users with roles.", len(user_roles))
        logger.info("Loaded execution data for %s users.", len(user_processes))

        role_execute_map, role_request_map = build_mappings(
            user_roles,
            user_processes,
            all_process_ids,
        )

        logger.info("Role execution assignments: %s", {
            role: len(processes) for role, processes in role_execute_map.items()
        })
        logger.info("Role request assignments: %s", {
            role: len(processes) for role, processes in role_request_map.items()
        })
        clear_existing_edges(session, args.dry_run)

        create_role_edges(session, "CAN_EXECUTE", role_execute_map, args.dry_run)
        create_role_edges(session, "CAN_REQUEST", role_request_map, args.dry_run)

    if args.dry_run:
        logger.info("Dry-run completed. No changes were applied.")
    else:
        logger.info("Permission rewiring completed successfully.")

    db_manager.close_all()


if __name__ == "__main__":
    main()

