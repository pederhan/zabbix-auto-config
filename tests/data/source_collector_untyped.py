from zabbix_auto_config.models import Host

HOSTS = [
    {
        "hostname": "foo.example.com",
    },
    {
        "hostname": "bar.example.com",
    },
]


def collect(*args, **kwargs):
    for host in HOSTS:
        host["enabled"] = True
        host["siteadmins"] = ["bob@example.com"]
        host["properties"] = ["pizza"]
        source = kwargs.get("source")
        if source:
            host["properties"].append(source)
        yield Host(**host)