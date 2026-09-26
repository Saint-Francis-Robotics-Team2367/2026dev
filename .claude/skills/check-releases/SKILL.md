---
name: check-releases
description: Check whether newer RobotPy / WPILib 2027 releases or Phoenix6 / REVLib SystemCore vendordeps have shipped relative to the version pinned in pyproject.toml, and recommend whether to bump. Use when asked to check for updates or new releases, whether the 2027 beta / RC has dropped, whether SystemCore vendordeps exist yet, or whether it's time to move off alpha.
---

# Check 2027 releases

This repo tracks the **RobotPy / WPILib 2027 alpha** through the preseason (background in
[docs/2027-migration.md](../../../docs/2027-migration.md)). The dependency is pinned in
`pyproject.toml` under `[tool.robotpy] robotpy_version` and is bumped **deliberately** as
alpha → beta → RC → final land. This skill checks what is newer than the pin across the
sources that matter and recommends whether to act.

## What to check

### 1. Current pin
Read `robotpy_version` from `pyproject.toml`. It is the baseline for every comparison below.

### 2. RobotPy + vendordep Python bindings on PyPI (deterministic — run the script)
Run the bundled checker with the venv interpreter:

```powershell
& .\.venv\Scripts\python.exe .claude\skills\check-releases\check_pypi_releases.py
```

It checks three PyPI packages for the 2027 / SystemCore (Python 3.14) stack and prints a `STATUS:`
(and, at a milestone, a `SIGNAL:`) line for each:

- **robotpy** — newest `2027.*` release vs. the pin; flags a channel change (alpha → beta → …).
- **phoenix6** and **robotpy-rev** — the CTR / REV **Python** bindings that unblock real motor
  control. It reports whether the package's **SystemCore line** (phoenix6 ≥ 26.50, robotpy-rev
  2027.*) has a wheel that **installs on Python 3.14**: either `cp314`, or a stable-ABI
  `cp3X-abi3` wheel (phoenix6 ships abi3 only, so a literal `cp314` tag never appears). Matching
  "installs on 3.14" alone isn't enough, because phoenix6's roboRIO line is also abi3.

Trust this over the PyPI web pages **and over a summarizer** — both miss pre-releases, because
`info.version` shows the latest *stable* (a 2026.x / roboRIO line). The script lists the wheel
platforms and prints a `NOTE:` if there's no `win_amd64` wheel (so no local sim install).

### 3. WPILib 2027 (web)
RobotPy rides the WPILib release train. Check for a newer 2027 tag / announcement and note the
channel (alpha / beta / RC), skimming the changelog for API changes that would touch our code
(kinematics, controllers, Driver Station, NetworkTables):
- https://github.com/wpilibsuite/allwpilib/releases
- https://wpilib.org/blog

### 4. Java/C++ vendordep context (web — secondary; step 2 is authoritative)
The CTR / REV **Java/C++** vendordeps and WPILib itself ship *ahead of* the RobotPy Python bindings,
so a SystemCore vendordep existing here means the Python binding is likely **next** — not that it is
usable from this repo yet. Confirm real usability with **step 2's Python 3.14 wheel check**; use these only as
early warning and for the changelog of API changes:
- Phoenix6 (CTR): https://api.ctr-electronics.com/changelog · https://docs.ctr-electronics.com
- REVLib (REV): https://github.com/wpilibsuite/SystemcoreTesting/blob/main/REV.md · https://docs.revrobotics.com/revlib

## 5. How to read the result

Rank the signals by how much they should change what we do:

| Signal | Urgency | Action |
|--------|---------|--------|
| New **alpha** (channel unchanged) | low | Bump when convenient; expect continued churn. |
| First **beta** | **high** | API is stabilizing — bump promptly and start investing in code deferred because of churn. |
| **RC / final** | **high** | Bump and lock in; do a full pass over `docs/2027-migration.md` for last-minute renames. |
| Java/C++ SystemCore vendordep ships, but **no Python 3.14 wheel yet** | medium | Python binding likely next — keep watching `phoenix6` / `robotpy-rev` on PyPI (step 2). |
| **Python 3.14 wheel** (cp314 or abi3) for `phoenix6` / `robotpy-rev` appears (step 2 → `STATUS: AVAILABLE`) | **high** | Python binding is installable — plan the `swervemodule.py` swap (keep the `set_desired_state` / `get_state` / `get_position` interface). |
| SystemCore-2027 **go/no-go** news | — | Not a version bump, but surface it — the whole 2027 target depends on it. |

## 6. If bumping

1. Update `robotpy_version` in `pyproject.toml` to the new version.
2. Refresh cached robot-side wheels: `robotpy sync`.
3. Run the full gate (per CLAUDE.md): `robotpy test` + `pyright` + `black --check .`.
4. If anything broke, reconcile against the installed stubs (`.venv/Lib/site-packages/**/*.pyi`,
   **not** older docs) and record any real API changes in `docs/2027-migration.md`.
5. If the channel changed (e.g. "alpha" → "beta"), update the version wording in `CLAUDE.md` and the
   `docs/` pages so they don't drift.

## Output

Give a compact report: current pin, latest RobotPy 2027 (+ channel), WPILib status, vendordep status,
and a one-line recommendation — **hold**, **bump now**, or **bump + invest**. Cite the URLs for
anything found on the web.
