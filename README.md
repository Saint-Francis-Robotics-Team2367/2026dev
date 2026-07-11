# 2027Dev — FRC 2027 Robot Code (Python / RobotPy)

Command-based **swerve** robot code for the **2027 FRC season**, written in Python with
[RobotPy](https://robotpy.readthedocs.io/). Built simulation-first.

> 2027 replaces the roboRIO with **SystemCore** and RobotPy 2027 is still **alpha**
> (`2027.0.0a6`), so some APIs will shift before kickoff. See
> [docs/2027-migration.md](docs/2027-migration.md) for what changed.

## Requirements

- **Python 3.14**, 64-bit (RobotPy 2027 wheels are built for it).
- **Windows 11** (this repo's dev machine). macOS 15+ and recent 64-bit Linux also work — see
  [docs/2027-migration.md](docs/2027-migration.md#platform-support).
- **Git**, and on Windows the **Visual C++ 2022 redistributable (x64)**.

## Setup — from a fresh Windows 11 laptop

Everything is PowerShell, run from where you keep projects.

### 1. Install the prerequisites

Fastest path (winget ships with Windows 11), then **reopen PowerShell** so `PATH` updates:

```powershell
winget install --id Python.Python.3.14 -e
winget install --id Git.Git -e
winget install --id Microsoft.VCRedist.2015+.x64 -e
```

Prefer manual installers? Get Python from <https://www.python.org/downloads/> (check **“Add
python.exe to PATH”** and keep the **py launcher**), Git from <https://git-scm.com/download/win>,
and the VC++ redist from <https://aka.ms/vs/17/release/vc_redist.x64.exe>. Verify:

```powershell
py -3.14 --version   # -> Python 3.14.x
git --version
```

### 2. Clone the repo

```powershell
cd $HOME\Desktop
git clone <REPO-URL> 2027Dev   # replace <REPO-URL> with this repo's clone URL
cd 2027Dev
```

### 3. Create and activate the virtualenv

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **If activation errors** with *“running scripts is disabled on this system”* (the default on a
> fresh Windows), allow it for this shell and retry:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```
> Your prompt should then show `(.venv)`. (Alternatively, skip activation and call
> `.\.venv\Scripts\python.exe` directly.)

### 4. Install RobotPy + dev tools

```powershell
python -m pip install --upgrade pip
pip install --pre "robotpy[commands2]"   # --pre because 2027 is alpha
pip install black pre-commit pyright
robotpy sync         # caches robot-side artifacts (per pyproject.toml)
pre-commit install   # enables the Black format-on-commit hook
```

### 5. Verify

```powershell
python -c "import wpilib, commands2, wpimath; print(wpilib.__version__)"  # 2027.0.0a6.postN
robotpy test        # expect: 8 passed
pyright             # expect: 0 errors, 0 warnings
black --check .     # expect: All done / nothing to reformat
```

These four are exactly what CI enforces on every PR.

## Run the simulation

```powershell
robotpy sim
```

Opens the **WPILib Simulation GUI**. Two ways to see the robot move on the **Field2d** view:

- **Autonomous** — set the mode to *Autonomous* and enable. A controller-free demo routine drives
  the robot forward, strafes, and spins on its own (no controller needed).
- **Teleoperated** — set *Teleoperated* and drive with a plugged-in controller (or the GUI's
  keyboard/joystick widgets).

The drivetrain also publishes pose, chassis velocities, and module states to NetworkTables, so
**[Elastic](https://frc-elastic.gitbook.io/docs)** / AdvantageScope (connect to `localhost` in
sim) show the same telemetry. How the sim moves the robot is described in
[docs/simulation.md](docs/simulation.md).

## Tests & lint

```powershell
robotpy test        # WPILib full-boot smoke tests + swerve math/odometry tests (8 total)
black --check .     # formatting (WPILib/RobotPy standard)
pyright             # static type checking (standard mode)
```

`black` and `pyright` run as required PR checks (`.github/workflows/lint.yml`). Details and the
VS Code setup are in [docs/development.md](docs/development.md).

## Project layout

```
robot.py            # CommandRobot entry point (commands2.TimedCommandRobot)
robotcontainer.py   # wires subsystems, default commands, button bindings
constants.py        # geometry, kinematics, limits, hardware IDs, OI (placeholders)
subsystems/
  swervemodule.py   # one module (idealized kinematic sim model)
  drivetrain.py     # SwerveDrive4Kinematics + odometry + Field2d + heading sim
commands/
  drive.py          # default teleop command (field-relative, from Xbox sticks)
  auto.py           # controller-free autonomous demo (drives itself in sim)
telemetry.py        # publishes pose/chassis/module states to NT (Elastic/AdvantageScope)
tests/
  test_swerve.py    # kinematics / module / odometry math (HAL-free)
  robot_test.py     # generated WPILib full-boot smoke tests
```

See [docs/architecture.md](docs/architecture.md) for how these fit together.

## Status / TODO

- [ ] Modules are an **idealized kinematic sim** (perfect tracking) — swap to closed-loop control on
      Phoenix6/REVLib CAN vendordeps + a `DCMotorSim` model once they ship for 2027 SystemCore.
- [ ] Heading is integrated in sim (no gyro wired) — use the SystemCore onboard IMU on real hardware.
- [ ] Deploy is deferred (sim-only, no SystemCore hardware yet). Set the team number and validate a
      real deploy when hardware arrives.
- [ ] Bump the pinned alpha versions as betas/RCs land.

## Documentation

- [docs/architecture.md](docs/architecture.md) — command-based structure and data flow.
- [docs/simulation.md](docs/simulation.md) — how simulation works and how to extend it.
- [docs/development.md](docs/development.md) — tooling, linting, type-checking, CI, VS Code.
- [docs/2027-migration.md](docs/2027-migration.md) — SystemCore + the 2027 RobotPy API changes.
