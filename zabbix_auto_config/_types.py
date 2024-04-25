"""Custom types used by Zabbix Auto Config.

Leading underscore in module name to avoid name collision with built-in module `types`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Protocol
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import TypeAlias
from typing import TypedDict
from typing import runtime_checkable

from .models import Host

if TYPE_CHECKING:
    import multiprocessing


class ZabbixTag(TypedDict):
    tag: str
    value: str


ZabbixTags = Sequence[ZabbixTag]

ZacTag = Tuple[str, str]
ZacTags = Set[ZacTag]


@runtime_checkable
class SourceCollectorModule(Protocol):
    """Module that collects hosts from a source."""

    def collect(self, *args: Any, **kwargs: Any) -> List[Host]:
        """Collect hosts from the given source. Returns a list of Host objects"""
        ...


@runtime_checkable
class HostModifierModule(Protocol):
    """Module that modifies a Host object."""

    def modify(self, host: Host) -> Host:
        """Takes a Host object and returns a modified Host object."""
        ...


class HostModifier(NamedTuple):
    """An imported host modifier."""

    name: str
    module: HostModifierModule


class SourceHosts(TypedDict):
    """Hosts collected from a source."""

    source: str
    hosts: List[Host]


class QueueDict(TypedDict):
    """Queue information for the health check dict."""

    size: int


class HealthDict(TypedDict):
    """Application health dict used by `zabbix_auto_config.__init__.write_health`"""

    date: str
    date_unixtime: int
    pid: int
    cwd: str
    all_ok: bool
    processes: List[Dict[str, Any]]
    queues: List[QueueDict]
    failsafe: int


SourceHostsQueue: TypeAlias = "multiprocessing.Queue[SourceHosts]"
