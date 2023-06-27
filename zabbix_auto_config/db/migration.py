from __future__ import annotations

import logging
from typing import Callable, Dict, List, Tuple, TYPE_CHECKING

import psycopg2

from ..models import ZacSettings

if TYPE_CHECKING:
    from psycopg2 import connection as DBConnection
    from psycopg2 import cursor as Cursor


def get_zac_version() -> Tuple[int, int, int]:
    from ..__about__ import __version__

    res = __version__.split(".")
    if not len(res) == 3 or not all(v for v in res):
        raise Exception(f"'{__version__}' is an invalid semantic version.")
    major, minor, patch = res
    # Remove alpha, beta, rc, etc. from patch version
    patch = "".join(p for p in patch if p.isdigit())
    return int(major), int(minor), int(patch)


def get_connection(uri: str) -> DBConnection:
    return psycopg2.connect(uri)


def run_migrations(config: ZacSettings) -> None:
    """Runs all migrations."""
    try:
        version = get_zac_version()
    except Exception as e:
        logging.exception(
            "Unable to determine ZAC version: %s. Please report this issue.", e
        )
        exit(1)

    connection = get_connection(config.db_uri)
    try:
        with connection.cursor() as cursor:
            _do_run_migrations(cursor, version)
        connection.commit()
    except Exception as e:
        connection.rollback()
        logging.exception(
            "Unable to perform migrations: %s. Changes have been rolled back. Please report this issue.",
            e,
        )
        exit(1)
    finally:
        connection.close()

    # TODO: add rollback on failure


def _do_run_migrations(cursor: Cursor, version: Tuple[int, int, int]) -> None:
    def run(func: Callable[[Cursor], None], cursor: Cursor) -> None:
        """Logs the migration and runs it."""
        logging.debug("Running migration: %s", func.__name__)
        func(cursor)

    # Run through all migrations in order
    # E.g. 1.0.0 -> 1.0.1 -> 1.1.0 -> 1.1.1 -> 1.1.2 -> 2.0.0
    for major in range(version[0] + 1):
        for minor in range(version[1] + 1):
            for patch in range(version[2] + 1):
                if major in MIGRATIONS["major"]:
                    for migration in MIGRATIONS["major"][major]:
                        run(migration, cursor)
                if minor in MIGRATIONS["minor"]:
                    for migration in MIGRATIONS["minor"][minor]:
                        run(migration, cursor)
                if patch in MIGRATIONS["patch"]:
                    for migration in MIGRATIONS["patch"][patch]:
                        run(migration, cursor)


# TODO: determine which version we are on and which migrations we need to run


def _add_hosts_source_column_timestamp(cursor: Cursor) -> None:
    # Check if the timestamp column exists
    cursor.execute(
        """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='hosts_source' and column_name='timestamp';
    """
    )
    result = cursor.fetchone()

    # If the column does not exist, add it
    if not result:
        cursor.execute(
            """
            ALTER TABLE hosts_source 
            ADD COLUMN timestamp timestamp WITHOUT TIME ZONE NOT NULL DEFAULT now();
        """
        )
        logging.info("Added 'timestamp' column to 'hosts_source' table.")


MIGRATIONS = {
    "major": {
        1: [],
        2: [],
        3: [],
    },
    "minor": {
        1: [],
        2: [
            _add_hosts_source_column_timestamp,
        ],
        3: [],
    },
    "patch": {
        1: [],
        2: [],
        3: [],
    },
}  # type: Dict[str, Dict[int, List[Callable[[Cursor], None]]]]
