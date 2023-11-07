"""Compatibility helper module. 

Used to provide backwards compatibility with older versions of ZAC.
"""

import logging
from functools import lru_cache
import inspect
from typing import Any, Callable
from ._types import HostModifierDict

from zabbix_auto_config.models import Host
@lru_cache(maxsize=None)
def takes_kwargs(func: Callable[..., Any]) -> bool:
    """Returns True if the given function accepts keyword arguments."""
    logging.debug("We are in takes_kwargs")
    return any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in inspect.signature(func).parameters.values()
    )


def run_host_modifier(modifier: HostModifierDict, host: Host) -> Host:
    """Run a host modifier function for a given host."""
    func = modifier["module"].modify
    host = host.model_copy(deep=True)
    if takes_kwargs(func):
        return func(host=host, **modifier["config"])
    else:
        return func(host)