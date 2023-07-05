import multiprocessing
from pathlib import Path
from unittest.mock import patch, Mock

from zabbix_auto_config.models import SourceCollectorSettings
from zabbix_auto_config.processing import SourceMergerProcess


@patch("psycopg2.connect")
def test_source_merger_first_sleep_duration(mock_connect: Mock, tmp_path: Path):
    mock_connect.return_value = True  # we don't care about this right now

    source_collectors = {
        "source1": SourceCollectorSettings(
            module_name="source1",
            update_interval=11,
        ),
        "source2": SourceCollectorSettings(
            module_name="source2",
            update_interval=22,
        ),
        "source2": SourceCollectorSettings(
            module_name="source2",
            update_interval=33,
        ),
    }

    modifier_dir = tmp_path / "modifier_dir"
    modifier_dir.mkdir()

    process = SourceMergerProcess(
        name="test-source",
        state=multiprocessing.Manager().dict(),
        db_uri="",
        host_modifier_dir=modifier_dir,
        source_collectors=source_collectors,
    )
    assert process._first_sleep_duration() == 33
    process.source_collectors = {}
    assert process._first_sleep_duration() == 0
