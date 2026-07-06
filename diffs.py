"""Naive textual diff between a scenario's source and published artifact.

This is what a plain `diff` sees. phantom's verdict is computed separately;
contrasting the two is the point of the demo. On `clean` the text differs
(comments, spacing) yet phantom reports nothing, because its comparison is
semantic. On a tampered scenario the diff shows the injected code and phantom
pins it.
"""

from __future__ import annotations

import difflib
from pathlib import Path


def _tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(errors="replace")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def render_difference(source_dir: Path, artifact_dir: Path) -> list[str]:
    source = _tree(source_dir)
    artifact = _tree(artifact_dir)
    lines: list[str] = []
    for path, content in artifact.items():
        if path not in source:
            lines.append(f"+ new file in artifact: {path}")
            lines += [f"    {line}" for line in content.splitlines()]
        elif source[path] != content:
            lines += list(
                difflib.unified_diff(
                    source[path].splitlines(),
                    content.splitlines(),
                    fromfile=f"source/{path}",
                    tofile=f"artifact/{path}",
                    lineterm="",
                )
            )
    for path in source:
        if path not in artifact:
            lines.append(f"- removed in artifact: {path}")
    return lines or ["(byte-identical)"]
