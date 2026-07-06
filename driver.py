"""Scan a local scenario with phantom's public library API.

A scenario is a directory with source/ and artifact/ trees. They are served to
phantom through small Fetcher and SourceResolver implementations, which is
exactly how a new ecosystem or a private registry plugs into the tool without
touching its core. No network, fully deterministic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from phantom.core import exit_code_for, scan
from phantom.ecosystems.base import Ecosystem, Fetcher, SourceResolver
from phantom.models import Artifact, FileEntry, NoSource, ScanResult, SourceTree
from phantom.normalizers.base import Normalizer
from phantom.normalizers.python_ast import PythonASTNormalizer
from phantom.normalizers.raw import RawNormalizer
from phantom.report import json_report, sarif_report, table_report

SOURCE_REPO = "https://github.com/example/mylib"

_NORMALIZERS: dict[str, list[Normalizer]] = {
    "pypi": [PythonASTNormalizer()],
    "npm": [RawNormalizer((".js", ".mjs", ".cjs"))],
}


def _load(root: Path) -> list[FileEntry]:
    return [
        FileEntry(str(path.relative_to(root)), path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


class _LocalFetcher(Fetcher):
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir

    def fetch_artifact(self, pkg: str, version: str) -> Artifact:
        return Artifact(pkg, version, f"{pkg}-{version}", _load(self.artifact_dir), {})


class _LocalSourceResolver(SourceResolver):
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir

    def resolve_source(
        self, pkg: str, version: str, metadata: dict
    ) -> SourceTree | NoSource:
        return SourceTree(SOURCE_REPO, f"v{version}", _load(self.source_dir))


class LocalEcosystem(Ecosystem):
    def __init__(self, name: str, scenario_dir: Path) -> None:
        self.name = name
        self._fetcher = _LocalFetcher(scenario_dir / "artifact")
        self._source_resolver = _LocalSourceResolver(scenario_dir / "source")
        self._normalizers = _NORMALIZERS[name]

    @property
    def fetcher(self) -> Fetcher:
        return self._fetcher

    @property
    def source_resolver(self) -> SourceResolver:
        return self._source_resolver

    @property
    def normalizers(self) -> list[Normalizer]:
        return self._normalizers


def run_scenario(scenario_dir: Path, ecosystem: str) -> ScanResult:
    return scan(scenario_dir.name, "1.0.0", LocalEcosystem(ecosystem, scenario_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan one phantom demo scenario")
    parser.add_argument("scenario", type=Path, help="path to a scenarios/<name> dir")
    parser.add_argument("--ecosystem", choices=("pypi", "npm"), default="pypi")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--sarif", action="store_true")
    args = parser.parse_args()

    result = run_scenario(args.scenario, args.ecosystem)
    if args.json:
        print(json_report.render(result))
    elif args.sarif:
        print(sarif_report.render(result))
    else:
        print(table_report.render(result))
    return exit_code_for(result)


if __name__ == "__main__":
    raise SystemExit(main())
