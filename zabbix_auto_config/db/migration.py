"""Very simple migration system for ZAC. Only supports upgrading, not downgrading for now.

In the future, we should either use Alembic or write a migration system that
provides downgrading capabilities. For now, this is good enough.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Tuple, TYPE_CHECKING

import psycopg2

from ..models import ZacSettings

if TYPE_CHECKING:
    from psycopg2 import connection as DBConnection
    from psycopg2 import cursor as Cursor

SemverType = Tuple[int, int, int]

def get_zac_version() -> SemverType:
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


def _do_run_migrations(cursor: Cursor, version: SemverType) -> None:
    # Run through all migrations in order
    # E.g. 1.0.0 -> 1.0.1 -> 1.1.0 -> 1.1.1 -> 1.1.2 -> 2.0.0
    for version, migrations in MIGRATIONS.items():
        version_str = ".".join(str(v) for v in version)
        logging.debug("Running DB migrations for version: %s", version_str)
        for migration in migrations:
            logging.debug("Running DB migration: %s", migration.__name__)
            migration(cursor)


def _add_hosts_source_column_timestamp(cursor: Cursor) -> None:
    table = "hosts_source"
    column = "timestamp"

    # Check if the column exists
    cursor.execute(
        f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='{table}' and column_name='{column}';
    """
    )
    if cursor.fetchone():
        logging.debug("Column '%s' already exists in '%s' table.", column, table)
        return

    # Column does not exist, add it
    cursor.execute(
        f"""
        ALTER TABLE {table} 
        ADD COLUMN {column} timestamp WITHOUT TIME ZONE NOT NULL DEFAULT now();
    """
    )
    logging.info("Added '%s' column to '%s' table.", column, table)


# Mapping of migrations to run per version. Sorted by semver (major, minor, patch)
# Each migration is a function that takes a cursor and performs the migration
# Each migration function should be idempotent, and thus safe to run multiple times.
# Versions should be in ascending order.
_MIGRATIONS = {
    (0, 2, 0): [_add_hosts_source_column_timestamp],
}  # type: Dict[SemverType, List[Callable[[Cursor], None]]]

# Ensure keys are sorted by semver (major, minor, patch)
MIGRATIONS = {version: _MIGRATIONS[version] for version in sorted(_MIGRATIONS)}

# TODO: in the future we could store migrations in modules named after the semver
# they are for. E.g.
# * 0.2.0.py, 0.2.1.py, 0.3.0.py, etc. OR 0/2/0.py, 0/2/1.py, 0/3/0.py, etc.
