"""
Populate the `measurements_by_country` Cassandra table using existing data
from `measurements_by_location`.

Usage:
    python scripts/migrate_measurements_by_country.py
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import db_manager

SELECT_QUERY = """
SELECT country, city, date_partition, timestamp, sensor_id, temperature, humidity
FROM measurements_by_location
"""

INSERT_QUERY = """
INSERT INTO measurements_by_country
(country, date_partition, timestamp, city, sensor_id, temperature, humidity)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def ensure_partition(date_partition: str | None, timestamp: datetime) -> str:
    if date_partition:
        return date_partition
    return timestamp.strftime("%Y%m%d")


def migrate() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    session = db_manager.get_cassandra_session()
    session.set_keyspace(settings.CASSANDRA_KEYSPACE)

    logger.info("Fetching rows from measurements_by_location...")
    rows = session.execute(SELECT_QUERY)

    inserted = 0
    for row in rows:
        partition = ensure_partition(row.date_partition, row.timestamp)
        session.execute(
            INSERT_QUERY,
            (
                row.country,
                partition,
                row.timestamp,
                row.city,
                row.sensor_id,
                row.temperature,
                row.humidity,
            ),
        )
        inserted += 1
        if inserted % 1000 == 0:
            logger.info("Migrated %s rows...", inserted)

    logger.info("Migration completed. Total rows inserted: %s", inserted)
    db_manager.close_all()


if __name__ == "__main__":
    migrate()

