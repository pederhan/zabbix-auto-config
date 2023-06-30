"""Very simple migration system for ZAC. Only supports upgrading, not downgrading for now.

In the future, we should either use Alembic or write a migration system that
provides downgrading capabilities. For now, this is good enough.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import psycopg2

from ..models import ZacSettings
from ..__about__ import __version__

if TYPE_CHECKING:
    from psycopg2 import connection as DBConnection
    from psycopg2 import cursor as Cursor
    from typing import Final

SemverType = Tuple[int, int, int]


MIGRATIONS_TABLE = "schema_migrations"  # type: Final[str]


class MigrationError(Exception):
    pass


class MigrationFailedError(MigrationError):
    def __init__(
        self,
        migration_name: str,
        migration_version: SemverType,
        target_version: SemverType,
        current_version: SemverType,
    ) -> None:
        super().__init__(
            (
                f"Unable to run DB migration '{migration_name}' for version {semver_to_str(migration_version)} "
                f"in the process of upgrading to {semver_to_str(target_version)}. "
                f"Current version: {semver_to_str(current_version)}. "
                f"Please report this issue."
            )
        )


def get_zac_version() -> SemverType:
    return str_to_semver(__version__)


def str_to_semver(version: str) -> SemverType:
    res = version.split(".")
    if not len(res) == 3 or not all(v for v in res):
        raise Exception(f"'{version}' is an invalid semantic version.")
    major, minor, patch = res
    # Remove alpha, beta, rc, etc. from patch version
    patch = "".join(p for p in patch if p.isdigit())
    return int(major), int(minor), int(patch)


def semver_to_str(version: SemverType) -> str:
    return ".".join(str(v) for v in version)


def get_connection(uri: str) -> DBConnection:
    try:
        return psycopg2.connect(uri)
    except Exception as e:
        logging.exception("Unable to connect to database: %s", e)
        exit(1)


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
    schema_version = get_schema_version(cursor)
    logging.debug("Current DB schema version: %s", semver_to_str(schema_version))

    # TODO add debug log if no migrations are needed

    for migration_version, migrations in MIGRATIONS.items():
        if version <= schema_version:
            continue

        logging.debug(
            "Running DB migrations for version: %s",
            semver_to_str(migration_version),
        )

        if migration_exists(migration_version, cursor):
            logging.debug(
                "Migration for version %s has already been applied. Skipping.",
                semver_to_str(migration_version),
            )
            continue

        for migration in migrations:
            migration_name = migration.__name__
            logging.debug("Running DB migration: %s", migration_name)
            try:
                migration(cursor)
            except Exception as e:
                raise MigrationFailedError(
                    migration_name=migration_name,
                    migration_version=migration_version,
                    target_version=version,
                    current_version=schema_version,
                ) from e

        record_migration(cursor, migration_version)



def get_schema_version(cursor: Cursor) -> SemverType:
    create_migrations_table_if_not_exists(cursor)
    cursor.execute(f"SELECT version FROM {MIGRATIONS_TABLE} ORDER BY version DESC")
    result = cursor.fetchone()

    if result:
        try:
            return str_to_semver(result[0])
        except Exception as e:
            # We don't want to brick the application if we can't parse the version
            # but this is pretty bad, so we definitely need to log it.
            logging.exception(
                "Unable to convert DB schema version '%s' to semantic version: %s",
                result[0],  # is this guaranteed to be safe to index?
                e,
            )
    else:
        logging.info("No DB schema version found.")
    return (0, 0, 0)  # fall back on 0.0.0 if no schema or failed to convert


def create_migrations_table_if_not_exists(cursor: Cursor) -> None:
    if not table_exists(MIGRATIONS_TABLE, cursor):
        cursor.execute(
            f"""
            CREATE TABLE {MIGRATIONS_TABLE} (
                version varchar PRIMARY KEY,
                applied_at timestamp without time zone default now()
            );
            """
        )


def table_exists(table: str, cursor: Cursor) -> bool:
    cursor.execute(
        f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table}'
        );
        """
    )
    result = cursor.fetchone()

    if result:
        return bool(result[0])
    else:
        return False


def column_exists(column: str, table: str, cursor: Cursor) -> bool:
    cursor.execute(
        f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='{table}' and column_name='{column}';
    """
    )
    return True if cursor.fetchone() else False


def migration_exists(version: SemverType, cursor: Cursor) -> bool:
    cursor.execute(
        f"SELECT version FROM {MIGRATIONS_TABLE} WHERE version = %s;",
        (semver_to_str(version),),
    )
    return True if cursor.fetchone() else False


def record_migration(cursor: Cursor, version: SemverType) -> None:
    v = semver_to_str(version)
    try:
        cursor.execute(
            f"INSERT INTO {MIGRATIONS_TABLE} (version) VALUES (%s);",
            (v,),
        )
    except psycopg2.errors.UniqueViolation:
        logging.warning(
            "Migration for version %s has already been recorded. Skipping.", v
        )
    logging.info("Recorded migration for version: %s", v)


def _add_hosts_source_column_timestamp(cursor: Cursor) -> None:
    table = "hosts_source"
    column = "timestamp"

    if column_exists(column, table, cursor):
        logging.debug("Column '%s' already exists in '%s' table.", column, table)
        return

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
MIGRATIONS = {
    version: _MIGRATIONS[version] for version in sorted(_MIGRATIONS)
}  # type: Dict[SemverType, List[Callable[[Cursor], None]]]

# TODO: in the future we could store migrations in modules named after the semver
# they are for. E.g.
# * 0.2.0.py, 0.2.1.py, 0.3.0.py, etc. OR 0/2/0.py, 0/2/1.py, 0/3/0.py, etc.
