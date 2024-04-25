from __future__ import annotations

from typing import Protocol
from typing import Type
from typing import runtime_checkable

from zabbix_auto_config.sourcecollectors.base import BaseSourceCollector


@runtime_checkable
class SourceCollectorModule(Protocol):
    """Module that modifies a Host object."""

    SourceCollector: Type[BaseSourceCollector]
