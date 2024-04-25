from __future__ import annotations

from typing import Protocol
from typing import Type
from typing import runtime_checkable

from zabbix_auto_config.hostmodifiers.base import BaseModifier


@runtime_checkable
class HostModifierModule(Protocol):
    """Module that modifies a Host object."""

    Modifier: Type[BaseModifier]
