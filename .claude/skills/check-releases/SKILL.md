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

### 2. RobotPy on PyPI (deterministic — run the script)
Run the bundled checker with the venv interpreter:

```powershell
& .\.venv\Scripts\python.exe .claude\skills\check-releases\check_robotpy_pypi.py
```

It prints the pin, the latest `2027.*` release (pre-releases included), a `STATUS:` line, and —
when the release **channel** changes (e.g. alpha → beta) — a `SIGNAL:` line. Trust this over the
PyPI web page: PyPI's `info.version` shows the latest *stable* release (a 2026.x line), so the 2027
pre-releases are easy to miss by eye or via a summarizer.

### 3. WPILib 2027 (web)
RobotPy rides the WPILib release train. Check for a newer 2027 tag / announcement and note the
channel (alpha / beta / RC), skimming the changelog for API changes that would touch our code
(kinematics, controllers, Driver Station, NetworkTables):
- https://github.com/wpilibsuite/allwpilib/releases
- https://wpilib.org/blog

### 4. Phoenix6 / REVLib SystemCore vendordeps (web)
These unblock replacing the idealized `subsystems/swervemodule.py` with real motor control, and are
**not expected during alpha**. Check whether a **SystemCore / 2027** vendordep has shipped, and its
version:
- Phoenix6 (CTR): https://api.ctr-electronics.com/changelog · https://docs.ctr-electronics.com
- REVLib (REV): https://docs.revrobotics.com/revlib · REV's software downloads page

## 5. How to read the result

Rank the signals by how much they should change what we do:

| Signal | Urgency | Action |
|--------|---------|--------|
| New **alpha** (channel unchanged) | low | Bump when convenient; expect continued churn. |
| First **beta** | **high** | API is stabilizing — bump promptly and start investing in code deferred because of churn. |
| **RC / final** | **high** | Bump and lock in; do a full pass over `docs/2027-migration.md` for last-minute renames. |
| Phoenix6 / REVLib **SystemCore vendordep** ships | **high** | Unblocks the real motor layer; plan the `swervemodule.py` swap (keep the `set_desired_state` / `get_state` / `get_position` interface). |
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
