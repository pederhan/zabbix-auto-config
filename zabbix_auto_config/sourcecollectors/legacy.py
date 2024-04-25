"""Compatibility helper module.

Used to provide backwards compatibility with older versions of ZAC.
"""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Protocol
from typing import runtime_checkable

from zabbix_auto_config.models import Host
from zabbix_auto_config.models import Settings
from zabbix_auto_config.models import SourceCollectorSettings
from zabbix_auto_config.sourcecollectors.base import BaseSourceCollector


@runtime_checkable
class LegacySourceCollectorModule(Protocol):
    """Protocol type for legacy host modifier modules."""

    __name__: str
    __module__: str

    def collect(self, *args: Any, **kwargs: Any) -> List[Host]: ...


class LegacySourceCollectorCompat(BaseSourceCollector):
    """Wrapper around legacy host modifier functions that do not implement
    the BaseHostModifier interface."""

    collector: LegacySourceCollectorModule

    def __init__(
        self,
        name: str,
        config: SourceCollectorSettings,
        app_config: Settings,
        collector: LegacySourceCollectorModule,
    ) -> None:
        super().__init__(name, config, app_config)
        if not isinstance(collector, LegacySourceCollectorModule):
            # TODO: improve logging and error message
            raise TypeError(
                "LegacyHostModifierCompat must be used with a legacy host modifier."
            )
        self.collector = collector
        self.name = collector.__name__
        self.dict_config = self.config.model_dump(mode="json")

    def collect(self) -> List[Host]:
        return self.collector.collect(**self.dict_config)
