# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FRC **2027** robot code in **Python / RobotPy**: command-based, 4-module **swerve**, **simulation-first**.
The 2027 control system is **SystemCore** (not roboRIO), and RobotPy 2027 is **alpha** (`2027.0.0a7`) —
install with `--pre` and expect APIs to shift. No SystemCore hardware yet, so deploy is deferred and
everything runs in simulation.

## Environment & commands

Python **3.14** in a repo-root `.venv`. In this shell, prefer calling the venv interpreter directly
(shell activation does not persist between tool calls):

```powershell
& .\.venv\Scripts\python.exe -m <tool>       # e.g. robotpy / pytest / black / pyright
```

- **Run simulation (GUI):** `robotpy sim` — opens the WPILib Simulation GUI. Enable **Autonomous** to
  watch `demo_auto` drive the robot on Field2d (no controller needed). GUI can't run headless/CI.
- **Run all tests (headless):** `robotpy test` — swerve math, Phoenix module sim, and full-robot
  boot (~30 s). This is the boot/smoke gate; it constructs the whole robot and runs 15 s of autonomous.
- **Run one test:** `& .\.venv\Scripts\python.exe -m pytest tests/test_swerve.py::<name> -q` — the
  `test_swerve.py` and `test_swervemodule_sim.py` work under plain pytest. `tests/robot_test.py` needs `robotpy test`.
- **Type check:** `pyright` (config in `pyproject.toml`, `standard` mode). **Format:** `black .` /
  `black --check .`. Both are required PR checks (`.github/workflows/lint.yml`).
- **Verify a nontrivial change with all three:** `robotpy test` + `pyright` + `black --check .`.
- Dependencies live in `pyproject.toml` `[tool.robotpy]`; `robotpy sync` refreshes the cached
  robot-side wheels.

## 2027 API — DO NOT trust pre-2027 memory here

The 2027 API changed a lot; using old names produces code that fails silently or at runtime. **Verify
against the installed stubs** (`.venv/Lib/site-packages/**/*.pyi`), not older docs. Full list in
[docs/2027-migration.md](docs/2027-migration.md). The ones that bite:

- **`wpimath` is flattened** — no `wpimath.kinematics` / `.geometry` / `.controller` submodules;
  everything is top-level (`wpimath.SwerveDrive4Kinematics`, `wpimath.Pose2d`, `wpimath.PIDController`, …).
- **Renames:** `ChassisSpeeds` → `ChassisVelocities`; `SwerveModuleState` → `SwerveModuleVelocity`.
  Field-relative + skew are instance methods: `ChassisVelocities(...).to_robot_relative(gyro)` /
  `.discretize(dt)`. Kinematics method is `to_swerve_module_velocities(...)`.
- **Alpha 7 made the whole API snake_case**, including lifecycle hooks: `autonomous_init`,
  `teleop_init`, `simulation_periodic`. A camelCase override still type-checks but **never runs**.
  SmartDashboard is gone — `telemetry.log(...)` instead. Don't name a module `telemetry.py` (collides
  with RobotPy's `telemetry` package).
- **Controllers renamed** for the new Driver Station: `XboxController` → `NiDsXboxController`;
  `commands2.button.CommandXboxController` → `CommandNiDsXboxController`.
- **`robotInit` and `wpilib.run` were REMOVED.** Do robot setup in the **constructor**
  (`def __init__(self): super().__init__(); ...`). Launch via the `robotpy` CLI. Using `robotInit`
  silently no-ops (symptom: `AttributeError: no attribute 'container'` in `autonomous_init`).
- **No `pyfrc`** in the 2027 stack → there is no `physics.py`. Simulate via `simulation_periodic()`.

## Architecture

Command-based; the interesting flow spans several files:

- `robot.py` (`commands2.TimedCommandRobot`) builds `RobotContainer` in its constructor, and
  schedules/cancels the autonomous command in `autonomous_init`/`teleop_init`.
- `robotcontainer.py` wires subsystems + controls and exposes `get_autonomous_command()`.
- `subsystems/drivetrain.py` is the core: `drive()` runs inverse kinematics
  (field-relative → robot-relative → discretize → module velocities → desaturate → per-module
  `optimize`); `periodic()` updates `SwerveDrive4Odometry`, publishes the pose to Field2d, and calls
  telemetry; `simulation_periodic()` integrates heading + module distance in sim.
- `subsystems/swervemodule.py` is **Phoenix 6**: TalonFX drive (`VelocityVoltage`) + TalonFX steer
  (`PositionVoltage`, `REMOTE_CANCODER`, continuous wrap) + CANcoder. The Talons close the loops; the class
  converts m / m/s / rad ↔ mechanism rotations. In sim, `simulate(dt)` runs two `DCMotorSim`s from the
  Talons' output voltage and writes back via `sim_state`. Interface: `set_desired_state` / `get_state` /
  `get_position` / `simulate`.
- **Phoenix sim gotchas:** simulated devices run on **wall-clock time** (`robotpy test` fast-forwards,
  so module behavior is tested in real time in `test_swervemodule_sim.py`), and Phoenix takes its
  **enable from the WPILib DS** — enable the sim DS; never `unmanaged.feed_enable` alongside WPILib
  (motors cut out). CAN IDs must be 0–62.
- `drivetrain_telemetry.py` publishes pose / chassis / module states / heading / speed as NT struct topics
  (`Drivetrain/*`) for Elastic / AdvantageScope / Glass.
- `bench/` is a standalone CAN bench tool (own venv, phoenix6 without WPILib — if WPILib is importable
  Phoenix silently switches to simulated devices). Excluded from pyright.
- `constants.py` holds all geometry/limits/IDs as **documented placeholders** (units: meters, radians,
  seconds). `commands/` holds the teleop (`drive.py`) and autonomous (`auto.py`) commands.

## Conventions

- Real robot values (track width, gear ratios, CAN IDs) in `constants.py` are placeholders — swap for
  measured/tuned numbers, don't scatter magic numbers in code.
- WPILib-standard units everywhere: meters, radians, seconds.
- Deeper docs: [docs/architecture.md](docs/architecture.md), [docs/simulation.md](docs/simulation.md),
  [docs/development.md](docs/development.md), [docs/2027-migration.md](docs/2027-migration.md).
