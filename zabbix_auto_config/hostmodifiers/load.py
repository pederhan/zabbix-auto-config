from __future__ import annotations

import importlib
import logging
import os
import sys
from typing import List

from zabbix_auto_config.hostmodifiers.base import BaseHostModifier
from zabbix_auto_config.hostmodifiers.legacy import LegacyHostModifierCompat
from zabbix_auto_config.hostmodifiers.legacy import LegacyHostModifierModule
from zabbix_auto_config.hostmodifiers.types import HostModifierModule
from zabbix_auto_config.models import Settings


def load_host_modifiers(config: Settings) -> List[BaseHostModifier]:
    modifier_dir = config.zac.host_modifier_dir

    sys.path.append(modifier_dir)
    try:
        module_names = [
            filename[:-3]
            for filename in os.listdir(modifier_dir)
            if filename.endswith(".py") and filename != "__init__.py"
        ]
    except FileNotFoundError:
        logging.error("Host modifier directory %s does not exist.", modifier_dir)
        sys.exit(1)
    host_modifiers: List[BaseHostModifier] = []
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logging.error(
                "Unable to import host modifier module '%s' from '%s'",
                module_name,
                modifier_dir,
            )
            continue

        # Check if the module is a valid host modifier module
        if isinstance(module, HostModifierModule):
            modifier = module.HostModifier(config)
            logging.debug("Loaded host modifier: %s", modifier.name)
        # Check if module is a legacy host modifier module (deprecated)
        elif isinstance(module, LegacyHostModifierModule):
            modifier = LegacyHostModifierCompat(config, module)
            logging.warning(
                "Module '%s' is a legacy host modifier module. Legacy support is deprecated and will be removed in a future version.",
                module_name,
            )
        else:
            logging.warning(
                "Module '%s' is not a valid host modifier module. Skipping.",
                module_name,
            )
            continue
        host_modifiers.append(modifier)
    logging.info(
        "Loaded %d host modifiers: %s",
        len(host_modifiers),
        ", ".join([repr(modifier.name) for modifier in host_modifiers]),
    )
    return host_modifiers
