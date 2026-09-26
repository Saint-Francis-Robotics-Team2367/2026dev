#!/usr/bin/env python3
r"""Report the 2027 / SystemCore release status of the Python packages this repo tracks.

Checks three PyPI packages against what the 2027 (SystemCore, Python 3.14) stack
needs, deterministically -- eyeballing PyPI misleads here because pre-releases hide
inside the ``releases`` map and ``info.version`` shows the latest *stable* (2026.x /
roboRIO) line:

  * robotpy      -- compared against the pin in pyproject.toml.
  * phoenix6     -- CTR's Python binding. The SystemCore build is what unblocks real
                    motor control; we detect it by a release in the SystemCore line
                    (see _SYSTEMCORE_LINE) with a wheel that installs on Python 3.14:
                    cp314, or a stable-ABI cp3X-abi3 wheel (phoenix6 ships abi3).
  * robotpy-rev  -- REV's Python binding; same signal.

The Java/C++ vendordeps ship *ahead of* the Python bindings, so a SystemCore vendordep
existing on the CTR / REV side does NOT mean it is usable from this (RobotPy) repo yet.
This script answers the question that actually matters here: is there a wheel our 3.14
venv can install?

Usage:
    & .\.venv\Scripts\python.exe .claude\skills\check-releases\check_pypi_releases.py

Stdlib only (no ``packaging`` dependency) so it runs regardless of venv state.
Always exits 0 -- it is informational, not a gate.
"""

from __future__ import annotations

import json
import re
import tomllib
import urllib.request
from pathlib import Path

# .claude/skills/check-releases/<this file> -> repo root is 3 levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Ordering of release phases. Finals sort after every pre-release of the same base
# version; post-releases (see parse()) break ties above their base.
_PHASE_RANK = {"a": 0, "b": 1, "rc": 2}
_PHASE_NAME = {0: "alpha", 1: "beta", 2: "rc", 3: "final"}

# A constrained PEP 440 subset that covers all three packages' schemes:
# X.Y.Z with an optional aN / bN / rcN pre-release and an optional .postN suffix.
# (PyPI stores normalized versions, so "26.50.0-alpha-1" arrives as "26.50.0a1".)
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


def fetch_releases(package: str) -> dict:
    """Return PyPI's ``releases`` map {version: [file dicts]} for a package."""
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)["releases"]


def pinned_robotpy() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["robotpy"]["robotpy_version"]


def report_robotpy() -> None:
    """Compare the newest robotpy 2027.* release on PyPI against our pin."""
    print("robotpy")
    pinned = pinned_robotpy()
    pinned_key = parse(pinned)
    try:
        releases = fetch_releases("robotpy")
    except Exception as exc:  # network/DNS/timeout — stay informational
        print(f"  pinned:      {pinned}")
        print(f"  ERROR:       could not reach PyPI ({exc!r})")
        return

    keyed = [(k, v) for v in releases if (k := parse(v)) and k[0] == 2027]
    print(
        f"  pinned:      {pinned}"
        + (f"  ({channel(pinned_key)})" if pinned_key else "")
    )
    if not keyed:
        print("  latest 2027: (none found on PyPI)")
        return

    latest_key, latest_raw = max(keyed)
    print(f"  latest 2027: {latest_raw}  ({channel(latest_key)})")
    if pinned_key is None:
        print("  STATUS:      pin did not parse — compare manually")
    elif latest_key > pinned_key:
        note = ""
        if channel(latest_key) != channel(pinned_key):
            note = (
                f"  (channel {channel(pinned_key)} -> {channel(latest_key)}"
                " — stabilization milestone, SKILL.md step 5)"
            )
        print(f"  STATUS:      NEWER available ({pinned} -> {latest_raw}){note}")
    elif latest_key == pinned_key:
        print("  STATUS:      up to date")
    else:
        print(
            f"  STATUS:      pin is ahead of PyPI's latest 2027 ({latest_raw}) — verify"
        )


# First release of each package's SystemCore / 2027 line, as a parse() key prefix.
# Needed because "installs on 3.14" alone is not a SystemCore signal: phoenix6's
# roboRIO line (26.1 - 26.3) also ships cp310-abi3 wheels, which install on 3.14.
#   * phoenix6:    CTR versions by *its* year; 26.50.0a1 was the first SystemCore alpha
#                  (https://api.ctr-electronics.com/changelog).
#   * robotpy-rev: follows the RobotPy scheme, so the 2027 line is 2027.*.
_SYSTEMCORE_LINE = {"phoenix6": (26, 50), "robotpy-rev": (2027, 0)}

# Wheel filename: {name}-{ver}(-{build})?-{python tag}-{abi tag}-{platform tag}.whl
# Each tag may be a dot-separated set (e.g. "cp313.cp314").
_CP_TAG_RE = re.compile(r"^cp3(\d+)$")


def _py314_wheel(filename: str) -> str | None:
    """Platform tag if this wheel installs on CPython 3.14, else None.

    Accepts an exact cp314 build, a stable-ABI (abi3) build for any cp3X <= 3.14,
    and pure-Python py3 wheels.
    """
    if not filename.endswith(".whl"):
        return None
    parts = filename[: -len(".whl")].split("-")
    if len(parts) < 5:
        return None
    py_tags, abi_tags, plat = parts[-3].split("."), parts[-2].split("."), parts[-1]
    for py in py_tags:
        if py in ("py3", "py314"):
            return plat
        m = _CP_TAG_RE.match(py)
        if not m:
            continue
        minor = int(m.group(1))
        if minor == 14 or ("abi3" in abi_tags and minor <= 14):
            return plat
    return None


def _newest_py314(
    package: str,
    parsed: list[tuple[tuple[int, int, int, int, int, int], str, list]],
) -> tuple[tuple[int, int, int, int, int, int], str, list[str]] | None:
    """Newest SystemCore-line (key, version, platforms) installable on Python 3.14."""
    line = _SYSTEMCORE_LINE.get(package, (0, 0))
    cands = []
    for k, v, files in parsed:
        if k[:2] < line:
            continue
        plats = sorted(
            {p for f in files if (p := _py314_wheel(f.get("filename") or ""))}
        )
        if plats:
            cands.append((k, v, plats))
    return max(cands, key=lambda t: t[0]) if cands else None


def report_vendordep(package: str) -> None:
    """Report whether a package has a Python 3.14 (2027/SystemCore) wheel yet."""
    print(package)
    try:
        releases = fetch_releases(package)
    except Exception as exc:  # network/DNS/timeout — stay informational
        print(f"  ERROR:        could not reach PyPI ({exc!r})")
        return

    parsed = [(k, v, releases[v]) for v in releases if (k := parse(v))]
    if not parsed:
        print("  (no parseable versions found)")
        return

    latest_key, latest_raw, _ = max(parsed, key=lambda t: t[0])
    print(f"  latest:       {latest_raw}  ({channel(latest_key)})")

    best = _newest_py314(package, parsed)
    if best is None:
        print("  py3.14 wheel: none")
        print(
            "  STATUS:       no SystemCore/2027 Python binding on PyPI yet"
            " (no Python 3.14-installable wheel in the SystemCore line)"
        )
    else:
        best_key, best_raw, plats = best
        print(f"  py3.14 wheel: {best_raw}  ({channel(best_key)})")
        print(f"  platforms:    {', '.join(plats)}")
        print("  STATUS:       AVAILABLE — installable on our Python 3.14 / 2027 stack")
        if not any(p.startswith("win_amd64") or p == "any" for p in plats):
            print("  NOTE:         no win_amd64 wheel — not installable for local sim")
        print("  SIGNAL:       plan the swervemodule.py swap (SKILL.md step 5)")


def main() -> int:
    report_robotpy()
    print()
    report_vendordep("phoenix6")
    print()
    report_vendordep("robotpy-rev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
