def modify(host, **kwargs):
    if host.hostname == "bar.example.com":
        host.properties.add("barry")
    return host
