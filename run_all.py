"""Run every scenario: show the difference, then phantom's verdict.

The contrast is the demo. On `clean` the files differ textually but phantom
reports nothing, because it compares semantics, not bytes. On the tampered
scenarios phantom pins the injected code as critical and locates it. The script
also self-checks every verdict and exits non-zero if a scenario stops behaving
as documented, so CI catches a phantom regression or a broken fixture.
"""

from __future__ import annotations

from pathlib import Path

from phantom.core import exit_code_for
from phantom.models import FindingType, ScanResult, Severity

from diffs import render_difference
from driver import run_scenario

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

# name, ecosystem, expected exit code, expected finding type, expected severity
SCENARIOS = [
    ("clean", "pypi", 0, None, None),
    ("phantom-file", "pypi", 1, FindingType.PHANTOM_FILE, Severity.CRITICAL),
    ("phantom-span", "pypi", 1, FindingType.PHANTOM_SPAN, Severity.CRITICAL),
    ("suspicious-pth", "pypi", 1, FindingType.SUSPICIOUS_PTH, Severity.CRITICAL),
    ("npm-injection", "npm", 1, FindingType.PHANTOM_FILE, Severity.CRITICAL),
]


def _verdict(result: ScanResult) -> list[str]:
    if not result.findings:
        return ["phantom: no findings (artifact matches source)"]
    out = [
        f"phantom: {len(result.findings)} finding(s), "
        f"highest severity {result.highest_severity.value}"
    ]
    for finding in result.findings:
        location = finding.path or "-"
        if finding.start_line:
            location += f":{finding.start_line}-{finding.end_line}"
        out.append(f"  [{finding.severity.value.upper()}] {finding.type.value} {location}")
        if finding.execution_vectors:
            out.append(f"    vectors: {', '.join(finding.execution_vectors)}")
    return out


def main() -> int:
    all_ok = True
    for name, ecosystem, exp_exit, exp_type, exp_sev in SCENARIOS:
        scenario = SCENARIOS_DIR / name
        result = run_scenario(scenario, ecosystem)
        code = exit_code_for(result)
        ok = code == exp_exit
        if exp_type is not None:
            ok = ok and any(
                f.type == exp_type and f.severity == exp_sev for f in result.findings
            )
        all_ok = all_ok and ok

        print(f"=== {name} ({ecosystem}) ===")
        print("difference (naive text diff of source vs published artifact):")
        for line in render_difference(scenario / "source", scenario / "artifact"):
            print(f"    {line}")
        for line in _verdict(result):
            print(line)
        print(f"self-check: {'PASS' if ok else 'FAIL'} (exit {code}, expected {exp_exit})")
        print()

    print("all scenarios behaved as documented" if all_ok else "SCENARIOS DIVERGED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
