from zabbix_auto_config.models import Host


def modify(host: Host, **kwargs) -> Host:
    if host.hostname == "bar.example.com":
        host.properties.add("barry")
    return host
