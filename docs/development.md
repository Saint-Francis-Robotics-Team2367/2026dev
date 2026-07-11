# Development

## Tooling overview

| Tool | Purpose | Command |
|------|---------|---------|
| `black` | Formatting (WPILib/RobotPy standard) | `black .` / `black --check .` |
| `pyright` | Static type checking (standard mode) | `pyright` |
| `pre-commit` | Runs Black automatically on commit | `pre-commit install` once |
| `robotpy test` | Boot smoke tests + our unit tests | `robotpy test` |

All are pinned: Black `26.5.1` (in `pyproject.toml`, `.pre-commit-config.yaml`, and CI),
pyright config in `pyproject.toml` (`[tool.pyright]`, `pythonVersion = 3.14`).

## Type checking

RobotPy ships `py.typed` markers and stubs, so pyright fully resolves `wpilib` / `wpimath` /
`commands2`. This is high-value here: it catches 2027 API drift (e.g. using the removed
`ChassisSpeeds` or `XboxController`) at edit/CI time instead of on the field. The generated
`tests/robot_test.py` is excluded from pyright because it does a library wildcard import.

## Continuous integration

`.github/workflows/lint.yml` runs on every PR and on pushes to `main`:

- **`black`** job — pure Python, runs on `ubuntu-latest`.
- **`pyright`** job — runs on **`windows-latest`**. It needs RobotPy installed to resolve types,
  and RobotPy's Linux wheels require **glibc ≥ 2.41** (Ubuntu 26.04 / Debian 13), newer than the
  current `ubuntu-latest` (24.04). Windows matches the local dev setup and installs cleanly.

## VS Code

RobotPy is CLI-first and editor-agnostic — nothing requires an IDE, and CI runs the same
commands. But VS Code is recommended, and the repo ships shared config in `.vscode/`
(`settings.json`, `extensions.json`, `launch.json` are committed; personal state is ignored):

- On open, VS Code recommends the **official WPILib extension** (`wpilibsuite.vscode-wpilib`),
  plus Python, Pylance, and the Black formatter. Accept the prompt.
- Select the `.venv` interpreter (Command Palette → *Python: Select Interpreter* →
  `.\.venv\Scripts\python.exe`).
- Pylance is the **same engine as our pyright gate**, pinned to `standard`, so in-editor errors
  match CI. Black formats on save.
- `F5` runs **robotpy sim** / **robotpy test** (`.vscode/launch.json`). The WPILib extension also
  adds *WPILib: Simulate Robot Code* / *Deploy* to the command palette — both wrap the same CLI.

### You don't need the full WPILib installer

For Python you do **not** need the full WPILib installer. The standalone RobotPy VS Code
extension was archived when Python support was folded into the official WPILib extension in 2024.
Java/C++ teams need the installer (GradleRIO toolchain); for Python, a normal VS Code + the
extensions above + our `.venv` is enough. A "tools-only" install is the most you'd want, and only
for utilities like the Driver Station / imaging tools.

## Conventions

- Command-based: logic lives in subsystems/commands, wired in `RobotContainer`. Keep `robot.py`
  thin.
- Units are WPILib-standard: **meters, radians, seconds**.
- Constants (ports, geometry, gains) go in `constants.py`, not scattered in code.
- Verify non-trivial changes with `robotpy test` + `pyright` + `black --check .` before committing.
