"""Custom types used by Zabbix Auto Config. 

Leading underscore in module name to avoid name collision with built-in module `types`.
"""

from typing import Any, Dict, Protocol, TypedDict, runtime_checkable, List
from .models import Host, SourceCollectorSettings


@runtime_checkable
class SourceCollectorModule(Protocol):
    """Module that collects hosts from a source."""

    def collect(self, *args: Any, **kwargs: Any) -> List[Host]:
        """Collect hosts from the given source. Returns a list of Host objects"""
        ...


@runtime_checkable
class HostModifierModule(Protocol):
    """Module that modifies a Host object."""

    def modify(self, host: Host, *args, **kwargs) -> Host:
        """Takes a Host object and returns a modified Host object."""
        ...


class HostModifierDict(TypedDict):
    """The dict created by
    `zabbix_auto_config.processing.SourceMergerProcess.get_host_modifiers`
    for each imported host modifier module."""

    name: str
    module: HostModifierModule
    config: Dict[str, Any] # derived from HostModifierSettings, but serialized to dict


class SourceCollectorDict(TypedDict):
    """The dict created by `zabbix_auto_config.get_source_collectors` for each
    imported source collector module."""

    name: str
    module: SourceCollectorModule
    config: SourceCollectorSettings
