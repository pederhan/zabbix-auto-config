"""Compatibility helper module.

Used to provide backwards compatibility with older versions of ZAC.
"""

from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable

from zabbix_auto_config.hostmodifiers.base import BaseModifier
from zabbix_auto_config.models import Host
from zabbix_auto_config.models import Settings


@runtime_checkable
class LegacyModifierModule(Protocol):
    """Protocol type for legacy host modifier modules."""

    __name__: str
    __module__: str

    def modify(self, host: Host) -> Host: ...


class LegacyCompatModifier(BaseModifier):
    """Wrapper around legacy host modifier functions that do not implement
    the BaseModifier interface."""

    modifier: LegacyModifierModule

    def __init__(self, config: Settings, modifier: LegacyModifierModule) -> None:
        super().__init__(config)
        if not isinstance(self, LegacyModifierModule):
            # TODO: improve logging and error message
            raise TypeError(
                "LegacyCompatModifier must be used with a legacy host modifier."
            )
        self.modifier = modifier
        self.name = modifier.__name__

    def modify(self, host: Host) -> Host:
        return self.modifier.modify(host)
