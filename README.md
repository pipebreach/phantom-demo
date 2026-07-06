# phantom-demo

A runnable demonstration of [`pipebreach/phantom`](https://github.com/pipebreach/phantom):
a supply-chain tool that detects when a package's **published artifact diverges
from its declared source**. This repo proves the tool works end to end, without
publishing anything malicious to a real registry.

It shows two things:

1. **Integration** (`verify-deps` workflow): a real GitHub Actions job that
   consumes the published `pipebreach/phantom@v0.2.0` Action to verify a live
   PyPI dependency and upload SARIF.
2. **Detection** (`scenarios` workflow): controlled, offline scenarios where a
   tampered artifact is scanned against a clean source, covering the full
   finding taxonomy.

## The scenarios

Each folder under `scenarios/` holds a `source/` tree (what the repo declares)
and an `artifact/` tree (what got published). `driver.py` serves both to phantom
through the library API, so the scan is deterministic and needs no network.

| Scenario | What was tampered | phantom verdict |
|----------|-------------------|-----------------|
| `clean` | nothing; artifact matches source (only comments/spacing differ) | no findings, exit 0 |
| `phantom-file` | an extra `_telemetry.py` that reads env vars and POSTs them out | `critical` `phantom_file` |
| `phantom-span` | a `_beacon()` function injected into an existing `core.py` | `critical` `phantom_span` with line numbers |
| `suspicious-pth` | a `.pth` file shipped in the artifact (runs at interpreter startup) | `critical` `suspicious_pth` |
| `npm-injection` | an extra `telemetry.js` exfiltrating `process.env` via `fetch` | `critical` `phantom_file` (npm) |

The point: none of the injected code is flagged for *looking* malicious. It is
flagged because it is not in the source. That is what catches clean, obfuscated,
or never-before-seen injection.

## Run it locally

```bash
pip install phantom-scan==0.2.0

# Run every scenario and self-check the verdicts
python run_all.py

# Inspect one scenario (add --json or --sarif)
python driver.py scenarios/phantom-span
python driver.py scenarios/npm-injection --ecosystem npm
```

Example (`scenarios/phantom-span`):

```
CRITICAL  phantom_span  high  mylib/core.py:9-14
    reason: injected top-level code `_beacon` at lines 9-14 of mylib/core.py is
    not present in mylib/core.py of https://github.com/example/mylib@v1.0.0;
    reads local data AND has network egress (exfiltration shape)
```

## How the offline scan works

`driver.py` implements phantom's `Fetcher` and `SourceResolver` interfaces over
local directories and bundles them into a `LocalEcosystem`. `phantom.core.scan()`
speaks only those interfaces, so pointing it at local trees (or, later, a private
registry) needs no change to phantom itself. That is the same plugin seam the
tool uses to add new ecosystems.

## CI

- **`scenarios`** installs `phantom-scan==0.2.0` and runs `run_all.py`. Green
  means phantom's verdicts still match the documented outcomes.
- **`verify-deps`** runs the `pipebreach/phantom@v0.2.0` Action against
  `phantom-scan==0.2.0` itself and uploads SARIF. Green means the Action
  integrates and the dependency's artifact matches its source.
