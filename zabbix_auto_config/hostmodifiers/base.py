from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod

from zabbix_auto_config.models import Host
from zabbix_auto_config.models import HostModifierSettings
from zabbix_auto_config.models import Settings


class BaseModifier(ABC):
    def __init__(self, app_config: Settings) -> None:
        self.app_config = app_config
        self.name = __name__
        self.logger = logging.getLogger(__name__)
        conf = app_config.host_modifiers.get(self.name, None)
        if not conf:
            self.logger.debug("No configuration found for host modifier %s", self.name)
            conf = HostModifierSettings()
        self.config = conf

    @abstractmethod
    def modify(self, host: Host) -> Host:
        raise NotImplementedError
