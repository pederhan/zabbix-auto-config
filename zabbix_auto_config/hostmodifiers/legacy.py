"""Compatibility helper module.

Used to provide backwards compatibility with older versions of ZAC.
"""

from __future__ import annotations

import inspect
import logging
from functools import lru_cache
from typing import Any
from typing import Callable
from typing import Protocol
from typing import runtime_checkable

from zabbix_auto_config.hostmodifiers.base import BaseModifier
from zabbix_auto_config.models import Host
from zabbix_auto_config.models import Settings


@lru_cache(maxsize=None)
def takes_kwargs(func: Callable[..., Any]) -> bool:
    """Returns True if the given function accepts keyword arguments."""
    logging.debug("We are in takes_kwargs")
    return any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in inspect.signature(func).parameters.values()
    )


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
