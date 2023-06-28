from zabbix_auto_config.db.migration import MIGRATIONS


def test_migrations_are_sorted():
    """Migrations should be sorted by semantic versioning."""
    versions = list(MIGRATIONS.keys())
    assert versions == sorted(versions)

def test_run_migrations_mock():
    # TODO: mock database connection and cursor
    # OR: use a real database (how in GitHub Actions?)