from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from typing import List

from pydantic import RootModel

from zabbix_auto_config.models import Host
from zabbix_auto_config.models import Settings
from zabbix_auto_config.models import SourceCollectorSettings


class BaseSourceCollector(ABC):
    def __init__(
        self,
        name: str,
        config: SourceCollectorSettings,
        app_config: Settings,
    ) -> None:
        self.name = name
        self.config = config
        self.app_config = app_config
        self.logger = logging.getLogger(self.name)

    @abstractmethod
    def collect(self) -> List[Host]:
        raise NotImplementedError

    def collect_as_json(self) -> str:
        return RootModel[List[Host]](self.collect()).model_dump_json(indent=2)
