from typing import Any, Callable

import pytest
from zabbix_auto_config.compat import takes_kwargs
from zabbix_auto_config.models import Host

def host_modifier_kwargs(host: Host, **kwargs) -> Host:
    pass

def host_modifer_no_kwargs(host: Host) -> Host:
    pass

@pytest.mark.parametrize(
    "func,expected",
    [
        pytest.param(host_modifier_kwargs, True, id="Kwargs"),
        pytest.param(host_modifer_no_kwargs, False, id="No kwargs"),
    ],
)
def test_takes_kwargs(func: Callable[..., Any], expected: bool) -> None:
    assert takes_kwargs(func) == expected



def test_run_host_modifier() -> None:
    class MockKwargsModule:
        def modify(self, host: Host, **kwargs) -> Host:
            pass
    class MockKwargsModule:
        def modify(self, host: Host, **kwargs) -> Host:
            pass

    modifier_dict = {
        "module": "foo",
        "config": {"foo", "bar"},
    }
    raise NotImplementedError("IMPLEMENT ME")