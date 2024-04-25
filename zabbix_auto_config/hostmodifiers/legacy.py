"""Compatibility helper module.

Used to provide backwards compatibility with older versions of ZAC.
"""

from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable

from zabbix_auto_config.hostmodifiers.base import BaseHostModifier
from zabbix_auto_config.models import Host
from zabbix_auto_config.models import Settings


@runtime_checkable
class LegacyHostModifierModule(Protocol):
    """Protocol type for legacy host modifier modules."""

    __name__: str
    __module__: str

    def modify(self, host: Host) -> Host: ...


class LegacyHostModifierCompat(BaseHostModifier):
    """Wrapper around legacy host modifier functions that do not implement
    the BaseHostModifier interface."""

    modifier: LegacyHostModifierModule

    def __init__(self, config: Settings, modifier: LegacyHostModifierModule) -> None:
        super().__init__(config)
        if not isinstance(modifier, LegacyHostModifierModule):
            # TODO: improve logging and error message
            raise TypeError(
                "LegacyHostModifierCompat must be used with a legacy host modifier."
            )
        self.modifier = modifier
        self.name = modifier.__name__

    def modify(self, host: Host) -> Host:
        return self.modifier.modify(host)
