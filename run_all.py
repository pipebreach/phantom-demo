"""Run every scenario and check phantom's verdict matches what we documented.

Doubles as the demo's self-test: exits non-zero if any scenario diverges from
its expected outcome, so CI catches a phantom regression or a broken fixture.
"""

from __future__ import annotations

from pathlib import Path

from phantom.core import exit_code_for
from phantom.models import FindingType, Severity

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


def main() -> int:
    all_ok = True
    for name, ecosystem, exp_exit, exp_type, exp_sev in SCENARIOS:
        result = run_scenario(SCENARIOS_DIR / name, ecosystem)
        code = exit_code_for(result)
        ok = code == exp_exit
        if exp_type is not None:
            ok = ok and any(
                f.type == exp_type and f.severity == exp_sev for f in result.findings
            )
        all_ok = all_ok and ok

        if not result.findings:
            summary = "clean"
        else:
            summary = ", ".join(
                f"{f.severity.value}:{f.type.value}"
                + (f" @{f.start_line}-{f.end_line}" if f.start_line else "")
                for f in result.findings
            )
        print(f"[{'PASS' if ok else 'FAIL'}] {name:16} exit={code}  {summary}")

    print()
    print("all scenarios behaved as documented" if all_ok else "SCENARIOS DIVERGED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
