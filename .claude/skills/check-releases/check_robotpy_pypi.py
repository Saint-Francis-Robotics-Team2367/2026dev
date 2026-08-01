#!/usr/bin/env python3
r"""Report RobotPy 2027 releases on PyPI relative to the version pinned in pyproject.toml.

Why this exists: PyPI's ``info.version`` for ``robotpy`` points at the latest
*stable* release (a 2026.x line), and the 2027 releases are pre-releases tucked
inside the ``releases`` map. Eyeballing the PyPI page (or asking a summarizer)
routinely misses them. This script parses the full ``releases`` map, keeps only
the ``2027.*`` versions, PEP 440-sorts them, and compares against our pin.

Usage:
    & .\.venv\Scripts\python.exe .claude\skills\check-releases\check_robotpy_pypi.py

Stdlib only (no ``packaging`` dependency) so it runs regardless of venv state.
Always exits 0 — it is informational, not a gate.
"""

from __future__ import annotations

import json
import re
import tomllib
import urllib.request
from pathlib import Path

PYPI_URL = "https://pypi.org/pypi/robotpy/json"
# .claude/skills/check-releases/check_robotpy_pypi.py -> repo root is 3 levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Ordering of release phases. Finals sort after every pre-release of the same
# base version; post-releases (see parse()) break ties above their base.
_PHASE_RANK = {"a": 0, "b": 1, "rc": 2}
_PHASE_NAME = {0: "alpha", 1: "beta", 2: "rc", 3: "final"}

# RobotPy's versions are a constrained PEP 440 subset: YYYY.MINOR.PATCH with an
# optional aN / bN / rcN pre-release and an optional .postN suffix.
_VERSION_RE = re.compile(
    r"^(?P<year>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:(?P<pre>a|b|rc)(?P<pren>\d+))?"
    r"(?:\.post(?P<post>\d+))?$"
)


def parse(raw: str) -> tuple[int, int, int, int, int, int] | None:
    """Return a sortable key for a version string, or None if it doesn't fit."""
    m = _VERSION_RE.match(raw.strip())
    if not m:
        return None
    pre = m.group("pre")
    phase = _PHASE_RANK[pre] if pre else 3  # final (3) sorts after all pre-releases
    pre_num = int(m.group("pren")) if m.group("pren") else 0
    post = int(m.group("post")) if m.group("post") else 0
    return (
        int(m.group("year")),
        int(m.group("minor")),
        int(m.group("patch")),
        phase,
        pre_num,
        post,
    )


def channel(key: tuple[int, int, int, int, int, int]) -> str:
    return _PHASE_NAME[key[3]]


def pinned_raw() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["robotpy"]["robotpy_version"]


def main() -> int:
    pinned = pinned_raw()
    pinned_key = parse(pinned)

    try:
        with urllib.request.urlopen(PYPI_URL, timeout=30) as resp:
            payload = json.load(resp)
    except Exception as exc:  # network/DNS/timeout — stay informational
        print(f"pinned:      {pinned}")
        print(
            f"ERROR:       could not reach PyPI ({exc!r}) — check manually: {PYPI_URL}"
        )
        return 0

    keyed = []
    for raw in payload.get("releases", {}):
        key = parse(raw)
        if key and key[0] == 2027:
            keyed.append((key, raw))

    print(
        f"pinned:      {pinned}" + (f"  ({channel(pinned_key)})" if pinned_key else "")
    )
    if not keyed:
        print("latest 2027: (none found on PyPI)")
        return 0

    latest_key, latest_raw = max(keyed)
    print(f"latest 2027: {latest_raw}  ({channel(latest_key)})")

    if pinned_key is None:
        print("STATUS:      pinned version did not parse — compare manually")
    elif latest_key > pinned_key:
        print(f"STATUS:      NEWER available  ({pinned} -> {latest_raw})")
        if channel(latest_key) != channel(pinned_key):
            print(
                f"SIGNAL:      channel changed {channel(pinned_key)} -> {channel(latest_key)}"
                "  (stabilization milestone — see SKILL.md step 5)"
            )
    elif latest_key == pinned_key:
        print("STATUS:      up to date")
    else:
        print(
            f"STATUS:      pin is ahead of PyPI's latest 2027 ({latest_raw}) — verify the pin"
        )

    # Show the trailing few 2027 releases for context.
    recent = [r for _, r in sorted(keyed)][-6:]
    print("recent 2027: " + ", ".join(recent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
