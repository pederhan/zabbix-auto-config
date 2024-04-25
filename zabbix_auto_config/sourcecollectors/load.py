from __future__ import annotations

import importlib
import logging
import sys
from typing import List

from zabbix_auto_config.models import Settings
from zabbix_auto_config.sourcecollectors.base import BaseSourceCollector
from zabbix_auto_config.sourcecollectors.legacy import LegacySourceCollectorCompat
from zabbix_auto_config.sourcecollectors.legacy import LegacySourceCollectorModule
from zabbix_auto_config.sourcecollectors.types import SourceCollectorModule


def load_source_collectors(config: Settings) -> List[BaseSourceCollector]:
    source_collector_dir = config.zac.source_collector_dir
    sys.path.append(source_collector_dir)

    source_collectors: List[BaseSourceCollector] = []
    for (
        source_collector_name,
        source_collector_config,
    ) in config.source_collectors.items():
        try:
            module = importlib.import_module(source_collector_config.module_name)
        except ModuleNotFoundError:
            logging.error(
                "Unable to find source collector named '%s' in '%s'",
                source_collector_config.module_name,
                source_collector_dir,
            )
            continue
        if isinstance(module, SourceCollectorModule):
            source_collector = module.SourceCollector(
                source_collector_name, source_collector_config, config
            )
            logging.debug("Loaded source collector: %s", source_collector.name)
        elif isinstance(module, LegacySourceCollectorModule):
            source_collector = LegacySourceCollectorCompat(
                source_collector_name, source_collector_config, config, module
            )
            logging.warning(
                "Module '%s' is a legacy source collector module, which is deprecated. Please update the module to the new API.",
                source_collector_name,
            )
        else:
            logging.error(
                "Module '%s' is not a valid source collector module",
                source_collector_config.module_name,
            )
            continue
        source_collectors.append(source_collector)
    return source_collectors
